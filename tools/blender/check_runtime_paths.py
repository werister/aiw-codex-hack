"""Check the browser traffic sampler against the saved Blender airport meshes.

Before running this script, export samples from the real TypeScript sampler with
``node --experimental-strip-types``. The check is read-only: it never saves the
blend and uses display-metre coordinates from the airport manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree


REPO_ROOT = Path(__file__).resolve().parents[2]
BLENDER_DIR = REPO_ROOT / "tools" / "blender"
if str(BLENDER_DIR) not in sys.path:
    sys.path.insert(0, str(BLENDER_DIR))

import check_scene as geometry  # noqa: E402


TARGET_SCENE = "FRA · Airport demonstration"
GROUND_HEIGHT_MAX = 4.0
MOVEMENT_TOP_MIN = 1.65
MOVEMENT_TOP_MAX = 2.60
GROUND_ORIGIN_Z = 5.0
GROUND_RAY_LENGTH = 5.0
SAMPLE_STATES = (("25", True), ("25", False), ("07", True), ("07", False))
ROLES = ("arrive_north", "arrive_south", "depart_center", "depart_flex")
EXPECTED_RUNWAY_HITS = 20


def _args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True,
                        help="JSON exported from web/src/lib/airport-traffic.ts")
    parser.add_argument("--manifest", type=Path,
                        default=Path("web/public/models/airport/manifest.json"))
    parser.add_argument("--runtime-source", type=Path,
                        default=Path("web/src/lib/airport-traffic.ts"))
    parser.add_argument("--report", type=Path,
                        default=Path("assets/airport/runtime-verification.json"))
    return parser.parse_args(raw)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(values) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def _point_in_report(point):
    return [round(float(value), 5) for value in point]


def _movement_surface_bvh(root, depsgraph):
    """Build a BVH from actual upward-facing evaluated pavement triangles."""
    vertices = []
    polygons = []
    accepted_z = []
    source_triangle_count = 0
    for obj in geometry._descendants(root):
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        if mesh is None:
            continue
        try:
            mesh.calc_loop_triangles()
            matrix = evaluated.matrix_world
            for triangle in mesh.loop_triangles:
                points = tuple(matrix @ mesh.vertices[index].co for index in triangle.vertices)
                normal = (points[1] - points[0]).cross(points[2] - points[0])
                if normal.length <= 1e-10:
                    continue
                if normal.z / normal.length < 0.9:
                    continue
                z = sum(float(point.z) for point in points) / 3.0
                if not MOVEMENT_TOP_MIN <= z <= MOVEMENT_TOP_MAX:
                    continue
                source_triangle_count += 1
                accepted_z.append(z)
                base = len(vertices)
                vertices.extend(tuple(float(value) for value in point) for point in points)
                polygons.append((base, base + 1, base + 2))
        finally:
            evaluated.to_mesh_clear()
    if not polygons:
        return None, {"top_triangles": 0, "z_min": None, "z_max": None}
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=True)
    return tree, {
        "top_triangles": source_triangle_count,
        "z_min": round(min(accepted_z), 4),
        "z_max": round(max(accepted_z), 4),
    }


def _surface_hits(point, surfaces):
    origin = Vector((float(point[0]), float(point[1]), GROUND_ORIGIN_Z))
    direction = Vector((0.0, 0.0, -1.0))
    hits = {}
    for name, tree in surfaces.items():
        location, normal, _face, distance = tree.ray_cast(origin, direction, GROUND_RAY_LENGTH)
        if location is None or normal is None or normal.z < 0.9 or distance is None:
            continue
        if MOVEMENT_TOP_MIN <= location.z <= MOVEMENT_TOP_MAX:
            hits[name] = float(location.z)
    return hits


def _runtime_aircraft_matrix(position, tangent, scale):
    dx, dy, dz = (float(value) for value in tangent)
    yaw = math.atan2(-dx, dy)
    pitch = math.atan2(dz, math.hypot(dx, dy)) * min(1.0, max(0.0, (position[2] - 1.85) / 12.0))
    rotation = Euler((pitch, 0.0, yaw), "XYZ")
    scale_vector = Vector((scale, scale, scale))
    return Matrix.LocRotScale(Vector(position), rotation, scale_vector)


def _failure(failures, message):
    failures.append(message)


def run(args):
    started = time.monotonic()
    failures = []
    notes = []
    samples_path = args.samples.resolve()
    manifest_path = args.manifest.resolve()
    source_path = args.runtime_source.resolve()
    blend_path = Path(bpy.data.filepath).resolve()
    report_path = args.report.resolve()

    sample_document = json.loads(samples_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    source_hash = _sha256(source_path)
    manifest_hash = _sha256(manifest_path)
    blend_hash = _sha256(blend_path)
    if sample_document.get("source_sha256") != source_hash:
        _failure(failures, "Node samples were exported from a different airport-traffic.ts revision")
    if sample_document.get("manifest_sha256") != manifest_hash:
        _failure(failures, "Node samples were exported from a different browser airport manifest")
    assets_manifest_path = REPO_ROOT / "assets" / "airport" / "manifest.json"
    assets_manifest_hash = _sha256(assets_manifest_path)
    if assets_manifest_hash != manifest_hash:
        _failure(failures, "browser manifest and Blender asset manifest hashes differ")

    expected_states = [{"od": od, "r18Open": open_state} for od, open_state in SAMPLE_STATES]
    if sample_document.get("states") != expected_states:
        _failure(failures, f"sample states are not the four expected combinations: {sample_document.get('states')}")
    if sample_document.get("roles") != list(ROLES):
        _failure(failures, f"sample roles differ from runtime roles: {sample_document.get('roles')}")
    samples_per_group = int(sample_document.get("sample_count_per_role_and_state", 0))
    if samples_per_group != 1200:
        _failure(failures, f"expected 1,200 samples per state/role, found {samples_per_group}")

    grouped = defaultdict(list)
    for sample in sample_document.get("samples", []):
        key = (str(sample.get("od")), bool(sample.get("r18Open")), str(sample.get("role")))
        grouped[key].append(sample)
    expected_total = len(SAMPLE_STATES) * len(ROLES) * samples_per_group
    if len(sample_document.get("samples", [])) != expected_total:
        _failure(failures, f"expected {expected_total} runtime samples, found {len(sample_document.get('samples', []))}")
    for od, open_state in SAMPLE_STATES:
        for role in ROLES:
            key = (od, open_state, role)
            values = grouped[key]
            values.sort(key=lambda item: int(item.get("index", -1)))
            if len(values) != samples_per_group:
                _failure(failures, f"{key}: expected {samples_per_group} samples, found {len(values)}")
                continue
            for expected_index, sample in enumerate(values):
                if int(sample.get("index", -1)) != expected_index:
                    _failure(failures, f"{key}: sample index sequence breaks at {expected_index}")
                    break
                if not _finite(sample.get("position", ())) or len(sample.get("position", ())) != 3:
                    _failure(failures, f"{key} sample {expected_index} has invalid position")
                    break
                if not _finite(sample.get("tangent", ())) or len(sample.get("tangent", ())) != 3:
                    _failure(failures, f"{key} sample {expected_index} has invalid tangent")
                    break

    scene = bpy.data.scenes.get(TARGET_SCENE)
    if scene is None:
        _failure(failures, f"saved Blender scene {TARGET_SCENE!r} is missing")
        scene = bpy.context.scene
    old_frame = scene.frame_current
    old_window = bpy.context.window
    old_window_scene = old_window.scene if old_window else None
    try:
        if old_window and old_window.scene != scene:
            old_window.scene = scene
        scene.frame_set(1)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()

        runway_roots = {}
        surfaces = {}
        surface_metadata = {}
        apron = scene.objects.get("Surface.TaxiApron")
        if apron is None:
            _failure(failures, "Surface.TaxiApron root is missing")
        else:
            surfaces[apron.name], surface_metadata[apron.name] = _movement_surface_bvh(apron, depsgraph)
        for key, spec in manifest.get("runways", {}).items():
            root_name = spec.get("root")
            root = scene.objects.get(root_name) if root_name else None
            if root is None:
                _failure(failures, f"runway {key!r} root {root_name!r} is missing")
                continue
            runway_roots[key] = root.name
            surfaces[root.name], surface_metadata[root.name] = _movement_surface_bvh(root, depsgraph)
        for root_name, metadata in surface_metadata.items():
            if metadata["top_triangles"] == 0:
                _failure(f"{root_name} has no evaluated upward-facing movement-surface triangles")

        obstacle_bounds = {}
        obstacle_roots = [obj for obj in scene.objects
                          if obj.get("obstacle_kind") in geometry.OBSTACLE_KINDS]
        for obstacle in obstacle_roots:
            vertices = geometry._world_mesh_vertices(obstacle, depsgraph)
            bounds = geometry._bounds_from_vertices(vertices)
            hull = geometry._convex_hull_xy(vertices)
            if bounds is None or len(hull) < 3:
                _failure(failures, f"obstacle {obstacle.name!r} has no finite evaluated mesh hull")
                continue
            obstacle_bounds[obstacle.name] = (bounds, hull)
        if not obstacle_bounds:
            _failure(failures, "no semantic building/tree/parked-aircraft roots were found")

        aircraft_local = {}
        scales = manifest.get("display_scale", {})
        for role in ROLES:
            root = scene.objects.get("Flight." + role)
            if root is None:
                _failure(failures, f"Blender source aircraft Flight.{role} is missing")
                continue
            corners = geometry._local_bbox_corners(root, depsgraph)
            if corners is None:
                _failure(failures, f"Flight.{role} has no evaluated local mesh bounds")
                continue
            asset_scale = float(scales.get("moving_widebody" if role == "arrive_south" else "moving_narrowbody", 0.0))
            if not math.isfinite(asset_scale) or asset_scale <= 0:
                _failure(failures, f"manifest has no positive moving-aircraft scale for {role}")
                continue
            aircraft_local[role] = (corners, asset_scale)

        ground_totals = Counter()
        ground_misses = Counter()
        ground_miss_examples = []
        runway_hits = Counter()
        closed_west_hits = Counter()
        open_west_hits = Counter()
        obstacle_collisions = Counter()
        obstacle_examples = []
        pair_collisions = Counter()
        pair_examples = []
        min_obstacle_gap = (math.inf, None)
        min_pair_center_distance = (math.inf, None)
        direction_checks = {}
        state_reports = []

        axis_for = {}
        for key, spec in manifest["runways"].items():
            heading = math.radians(float(spec["heading"]))
            axis_for[key] = Vector((math.sin(heading), math.cos(heading), 0.0))

        for od, r18_open in SAMPLE_STATES:
            state_key = (od, r18_open)
            role_samples = {role: grouped[state_key + (role,)] for role in ROLES}
            if any(len(role_samples[role]) != samples_per_group for role in ROLES):
                continue
            state_hit_counts = Counter()
            state_ground_counts = Counter()
            state_collision_count = 0
            state_closed_west = 0
            expected_runway = {
                "arrive_north": "north",
                "arrive_south": "south",
                "depart_center": "center",
                "depart_flex": "west" if r18_open else "center",
            }
            final_tangent = {}

            for index in range(samples_per_group):
                dynamic = {}
                for role in ROLES:
                    sample = role_samples[role][index]
                    position = tuple(float(value) for value in sample["position"])
                    tangent = tuple(float(value) for value in sample["tangent"])
                    if index == samples_per_group - 1:
                        final_tangent[role] = tangent

                    if position[2] <= GROUND_HEIGHT_MAX:
                        ground_totals[state_key + (role,)] += 1
                        state_ground_counts[role] += 1
                        hits = _surface_hits(position, surfaces)
                        if not hits:
                            ground_misses[state_key + (role,)] += 1
                            if len(ground_miss_examples) < 12:
                                ground_miss_examples.append({
                                    "state": {"od": od, "r18_open": r18_open},
                                    "role": role,
                                    "index": index,
                                    "position": _point_in_report(position),
                                })
                        else:
                            for root_name in hits:
                                if root_name != "Surface.TaxiApron":
                                    runway_hits[state_key + (role, root_name)] += 1
                                    state_hit_counts[(role, root_name)] += 1
                            expected_name = runway_roots.get(expected_runway[role])
                            if expected_name and expected_name in hits:
                                runway_hits[state_key + (role, "expected:" + expected_name)] += 1
                                state_hit_counts[(role, "expected:" + expected_name)] += 1
                            west_name = runway_roots.get("west")
                            if role == "depart_flex" and west_name in hits:
                                if r18_open:
                                    open_west_hits[state_key] += 1
                                else:
                                    closed_west_hits[state_key] += 1
                                    state_closed_west += 1

                    if role not in aircraft_local:
                        continue
                    local_corners, asset_scale = aircraft_local[role]
                    matrix = _runtime_aircraft_matrix(position, tangent, asset_scale)
                    world_corners = [matrix @ corner for corner in local_corners]
                    if not all(geometry._finite_vector(point) for point in world_corners):
                        _failure(failures, f"{od}/R18-{r18_open}/{role} sample {index} has invalid aircraft hull")
                        continue
                    bounds = geometry._bounds_from_points(world_corners)
                    hull = geometry._convex_hull_xy(world_corners)
                    if bounds is None or len(hull) < 3:
                        _failure(failures, f"{od}/R18-{r18_open}/{role} sample {index} has empty aircraft hull")
                        continue
                    dynamic[role] = (Vector(position), bounds, hull)

                    for obstacle_name, (obstacle_box, obstacle_hull) in obstacle_bounds.items():
                        vertical_gap = geometry._interval_gap(bounds[2], obstacle_box[2])
                        horizontal_gap = geometry._convex_polygon_distance(hull, obstacle_hull)
                        gap = math.hypot(horizontal_gap, vertical_gap)
                        if gap < min_obstacle_gap[0]:
                            min_obstacle_gap = (gap, {
                                "od": od, "r18_open": r18_open, "role": role,
                                "obstacle": obstacle_name, "sample": index,
                            })
                        if vertical_gap <= 1e-4 and geometry._convex_polygons_overlap(hull, obstacle_hull):
                            obstacle_collisions[state_key] += 1
                            state_collision_count += 1
                            if len(obstacle_examples) < 12:
                                obstacle_examples.append({
                                    "state": {"od": od, "r18_open": r18_open},
                                    "role": role, "obstacle": obstacle_name, "index": index,
                                })

                roles_present = list(dynamic)
                for left_index, left_role in enumerate(roles_present):
                    for right_role in roles_present[left_index + 1:]:
                        left_center, left_bounds, left_hull = dynamic[left_role]
                        right_center, right_bounds, right_hull = dynamic[right_role]
                        distance = (left_center - right_center).length
                        if distance < min_pair_center_distance[0]:
                            min_pair_center_distance = (distance, {
                                "od": od, "r18_open": r18_open,
                                "roles": [left_role, right_role], "sample": index,
                            })
                        vertical_gap = geometry._interval_gap(left_bounds[2], right_bounds[2])
                        if vertical_gap <= 1e-4 and geometry._convex_polygons_overlap(left_hull, right_hull):
                            pair_collisions[state_key] += 1
                            if len(pair_examples) < 12:
                                pair_examples.append({
                                    "state": {"od": od, "r18_open": r18_open},
                                    "roles": [left_role, right_role], "index": index,
                                })

            for role, target_runway in expected_runway.items():
                target_name = runway_roots.get(target_runway)
                hits = state_hit_counts[(role, "expected:" + str(target_name))]
                if hits < EXPECTED_RUNWAY_HITS:
                    _failure(failures, f"{od}/R18-{r18_open}/{role} only hit expected runway {target_runway} "
                                       f"{hits} times while on ground")
            if not r18_open and state_closed_west:
                _failure(failures, f"{od}/R18-closed flexible departure touches Runway 18 "
                                   f"at {state_closed_west} ground samples")
            if r18_open and open_west_hits[state_key] < EXPECTED_RUNWAY_HITS:
                _failure(failures, f"{od}/R18-open flexible departure reaches Runway 18 only "
                                   f"{open_west_hits[state_key]} ground samples")

            direction_targets = {
                "arrive_north": "north",
                "arrive_south": "south",
                "depart_center": "center",
                "depart_flex": "west" if r18_open else "center",
            }
            direction_results = {}
            for role, runway_key in direction_targets.items():
                tangent = Vector(final_tangent.get(role, (0.0, 0.0, 0.0)))
                runway_axis = axis_for[runway_key].copy()
                if runway_key == "west":
                    expected = runway_axis
                else:
                    expected = runway_axis * (1.0 if od == "07" else -1.0)
                dot = tangent.dot(expected)
                direction_results[role] = round(float(dot), 5)
                if dot < 0.9:
                    _failure(failures, f"{od}/R18-{r18_open}/{role} final tangent does not align "
                                       f"with {runway_key} departure/arrival direction (dot={dot:.3f})")
            direction_checks[f"OD{od}-R18-{'open' if r18_open else 'closed'}"] = direction_results

            state_reports.append({
                "od": od,
                "runway_18_open": r18_open,
                "samples_per_role": samples_per_group,
                "ground_samples_by_role": dict(state_ground_counts),
                "expected_runway_ground_hits_by_role": {
                    role: int(state_hit_counts[(role, "expected:" + str(runway_roots.get(target)))])
                    for role, target in expected_runway.items()
                },
                "depart_flex_runway18_ground_hits": int(open_west_hits[state_key] if r18_open else state_closed_west),
                "static_obstacle_collisions": int(state_collision_count),
                "aircraft_hull_collisions": int(pair_collisions[state_key]),
                "final_tangent_alignment_dot": direction_results,
            })

        for key, count in ground_misses.items():
            _failure(failures, f"{key}: {count} of {ground_totals[key]} ground samples miss all actual movement surfaces")
        for state_key, count in obstacle_collisions.items():
            _failure(failures, f"{state_key}: {count} runtime aircraft hull samples intersect static obstacle hulls/Z intervals")
        for state_key, count in pair_collisions.items():
            _failure(failures, f"{state_key}: {count} runtime aircraft hull sample pairs overlap")

        if min_obstacle_gap[1] is not None:
            notes.append({"minimum_conservative_aircraft_to_obstacle_gap_m": round(min_obstacle_gap[0], 4),
                          "at": min_obstacle_gap[1]})
        if min_pair_center_distance[1] is not None:
            notes.append({"minimum_aircraft_center_distance_m": round(min_pair_center_distance[0], 4),
                          "at": min_pair_center_distance[1]})

    except Exception as exc:
        _failure(failures, f"checker raised {type(exc).__name__}: {exc}")
    finally:
        try:
            scene.frame_set(old_frame)
            bpy.context.view_layer.update()
            if old_window and old_window_scene and old_window.scene != old_window_scene:
                old_window.scene = old_window_scene
        except Exception as exc:
            notes.append({"restore_context": f"{type(exc).__name__}: {exc}"})

    ground_total = sum(ground_totals.values())
    ground_miss_total = sum(ground_misses.values())
    result = {
        "schema_version": 1,
        "result": "PASS" if not failures else "FAIL",
        "scope": "illustrative web runtime paths against this Blender scene; not an operational clearance claim",
        "evidence": {
            "blend_file": str(blend_path),
            "blend_sha256": blend_hash,
            "runtime_source": str(source_path),
            "runtime_source_sha256": source_hash,
            "browser_manifest": str(manifest_path),
            "browser_manifest_sha256": manifest_hash,
            "assets_manifest_sha256": assets_manifest_hash,
            "node_sample_file": str(samples_path),
            "node_sample_sha256": _sha256(samples_path),
            "blender_version": bpy.app.version_string,
            "scene": TARGET_SCENE,
            "state_count": len(SAMPLE_STATES),
            "role_count": len(ROLES),
            "samples_per_state_role": samples_per_group,
            "total_runtime_samples": len(sample_document.get("samples", [])),
        },
        "surface_geometry": surface_metadata if "surface_metadata" in locals() else {},
        "semantic_obstacles": len(obstacle_roots) if "obstacle_roots" in locals() else 0,
        "ground_surface_check": {
            "height_threshold_m": GROUND_HEIGHT_MAX,
            "samples_checked": ground_total,
            "misses": ground_miss_total,
            "coverage_percent": round(100.0 * (ground_total - ground_miss_total) / ground_total, 5) if ground_total else 0,
            "miss_examples": ground_miss_examples,
        },
        "runtime_states": state_reports,
        "closed_runway18_ground_hits": {
            f"OD{od}": int(closed_west_hits[(od, False)]) for od in ("25", "07")
        },
        "open_runway18_ground_hits": {
            f"OD{od}": int(open_west_hits[(od, True)]) for od in ("25", "07")
        },
        "direction_checks": direction_checks,
        "static_obstacle_collisions": {
            "count": int(sum(obstacle_collisions.values())),
            "examples": obstacle_examples,
        },
        "aircraft_hull_collisions": {
            "count": int(sum(pair_collisions.values())),
            "examples": pair_examples,
        },
        "minimum_clearance": notes,
        "failures": failures,
        "elapsed_seconds": round(time.monotonic() - started, 2),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "result": result["result"],
        "report": str(report_path),
        "ground_samples": ground_total,
        "ground_misses": ground_miss_total,
        "static_obstacle_collisions": result["static_obstacle_collisions"]["count"],
        "aircraft_hull_collisions": result["aircraft_hull_collisions"]["count"],
        "minimum_clearance": notes,
        "failures": failures[:20],
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2), flush=True)
    return 0 if not failures else 1


def main():
    args = _args()
    try:
        code = run(args)
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
