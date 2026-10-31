"""Conservative checks for demo-scene clearance and animation playback.

Run this from Blender after opening the saved airport scene.  The check uses
the illustrative scene's display-metre coordinates; it is not an operational
or CAD safety analysis.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector


RUNWAY_CLEARANCE = 12.0
AIRCRAFT_SEPARATION = 20.0
GROUND_HEIGHT_MAX = 4.0
PHASE_FRAMES = ((1, 1200), (1201, 2400), (2401, 3600))
FLIGHT_ROLES = ("arrive_north", "arrive_south", "depart_center", "depart_flex")
OBSTACLE_KINDS = {"building", "tree", "parked_aircraft"}


def _descendants(root):
    return [root, *root.children_recursive]


def _finite_vector(value):
    return all(math.isfinite(float(component)) for component in value)


def _world_mesh_vertices(root, depsgraph):
    """Return evaluated descendant mesh vertices in world coordinates."""
    vertices = []
    for obj in _descendants(root):
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        if mesh is None:
            continue
        try:
            matrix = evaluated.matrix_world
            vertices.extend(matrix @ vertex.co for vertex in mesh.vertices)
        finally:
            evaluated.to_mesh_clear()
    return vertices


def _bounds_from_vertices(vertices):
    if not vertices or not all(_finite_vector(vertex) for vertex in vertices):
        return None
    return tuple((min(vertex[axis] for vertex in vertices),
                  max(vertex[axis] for vertex in vertices)) for axis in range(3))


def _local_bbox_corners(root, depsgraph):
    """Cache mesh bbox corners relative to a moving aircraft root."""
    root_matrix = root.evaluated_get(depsgraph).matrix_world
    inverse = root_matrix.inverted_safe()
    corners = []
    for obj in _descendants(root):
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        matrix = inverse @ evaluated.matrix_world
        corners.extend(matrix @ Vector(corner) for corner in evaluated.bound_box)
    if not corners or not all(_finite_vector(corner) for corner in corners):
        return None
    return tuple(corners)


def _world_points_from_local_corners(root_matrix, local_corners):
    world = [root_matrix @ corner for corner in local_corners]
    if not world or not all(_finite_vector(corner) for corner in world):
        return None
    return world


def _bounds_from_points(world):
    if not world or not all(_finite_vector(point) for point in world):
        return None
    return tuple((min(corner[axis] for corner in world),
                  max(corner[axis] for corner in world)) for axis in range(3))


def _interval_gap(first, second):
    if first[1] < second[0]:
        return second[0] - first[1]
    if second[1] < first[0]:
        return first[0] - second[1]
    return 0.0


def _runway_polygon(spec, margin=0.0):
    heading = math.radians(float(spec["heading"]))
    along = Vector((math.sin(heading), math.cos(heading), 0.0))
    across = Vector((math.cos(heading), -math.sin(heading), 0.0))
    center = Vector((float(spec["center"][0]), float(spec["center"][1]), 0.0))
    half_length = float(spec["length"]) * 0.5 + margin
    half_width = float(spec["width"]) * 0.5 + margin
    points = [center - along * half_length - across * half_width,
              center + along * half_length - across * half_width,
              center + along * half_length + across * half_width,
              center - along * half_length + across * half_width]
    return [(float(point.x), float(point.y)) for point in points]


def _convex_hull_xy(points):
    """Monotone-chain convex hull from actual world points or bbox corners."""
    ordered = sorted(set((float(point[0]), float(point[1])) for point in points))
    if len(ordered) <= 2:
        return ordered

    def cross(origin, first, second):
        return ((first[0] - origin[0]) * (second[1] - origin[1]) -
                (first[1] - origin[1]) * (second[0] - origin[0]))

    lower = []
    for point in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 1e-10:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 1e-10:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def _convex_polygons_overlap(first, second, epsilon=1e-7):
    if len(first) < 3 or len(second) < 3:
        return False
    for polygon in (first, second):
        for index, point in enumerate(polygon):
            other = polygon[(index + 1) % len(polygon)]
            axis_x, axis_y = -(other[1] - point[1]), other[0] - point[0]
            axis_length = math.hypot(axis_x, axis_y)
            if axis_length <= 1e-10:
                continue
            first_projection = [x * axis_x + y * axis_y for x, y in first]
            second_projection = [x * axis_x + y * axis_y for x, y in second]
            if min(max(first_projection), max(second_projection)) < max(
                    min(first_projection), min(second_projection)) - epsilon * axis_length:
                return False
    return True


def _point_segment_distance(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared <= 1e-20:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    t = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) /
                     length_squared))
    closest = (start[0] + t * dx, start[1] + t * dy)
    return math.hypot(point[0] - closest[0], point[1] - closest[1])


def _convex_polygon_distance(first, second):
    if _convex_polygons_overlap(first, second):
        return 0.0
    minimum = math.inf
    for point, polygon in [(point, second) for point in first] + [(point, first) for point in second]:
        for index, start in enumerate(polygon):
            end = polygon[(index + 1) % len(polygon)]
            minimum = min(minimum, _point_segment_distance(point, start, end))
    return minimum


def _inside_expanded_runway(hull, spec, margin=RUNWAY_CLEARANCE):
    return _convex_polygons_overlap(hull, _runway_polygon(spec, margin))


def _runway_projection_gap(hull, spec, margin=RUNWAY_CLEARANCE):
    return _convex_polygon_distance(hull, _runway_polygon(spec, margin))


def _upward_planar_triangles(root, depsgraph):
    """Extract actual evaluated, upward-facing horizontal mesh triangles."""
    triangles = []
    for obj in _descendants(root):
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
                if not all(_finite_vector(point) for point in points):
                    continue
                z_values = [point.z for point in points]
                normal = (points[1] - points[0]).cross(points[2] - points[0])
                if (max(z_values) - min(z_values) <= 1e-5 and normal.length > 1e-10 and
                        normal.z / normal.length > 0.999):
                    xy = tuple((float(point.x), float(point.y)) for point in points)
                    triangles.append((sum(z_values) / 3.0, xy, obj.name))
        finally:
            evaluated.to_mesh_clear()
    return triangles


def _triangles_overlap_xy(first, second, epsilon=1e-5):
    """Separating-axis test; edge-only contact is not positive-area overlap."""
    for triangle in (first, second):
        for index, point in enumerate(triangle):
            other = triangle[(index + 1) % 3]
            edge_x, edge_y = other[0] - point[0], other[1] - point[1]
            axis_x, axis_y = -edge_y, edge_x
            axis_length = math.hypot(axis_x, axis_y)
            if axis_length <= 1e-10:
                continue
            first_projection = [x * axis_x + y * axis_y for x, y in first]
            second_projection = [x * axis_x + y * axis_y for x, y in second]
            overlap = min(max(first_projection), max(second_projection)) - max(
                min(first_projection), min(second_projection)
            )
            if overlap <= epsilon * axis_length:
                return False
    return True


def _triangle_bounds_xy(triangle):
    return (min(point[0] for point in triangle), max(point[0] for point in triangle),
            min(point[1] for point in triangle), max(point[1] for point in triangle))


def _triangle_bounds_overlap(first, second, epsilon=1e-5):
    return (first[0] < second[1] - epsilon and second[0] < first[1] - epsilon and
            first[2] < second[3] - epsilon and second[2] < first[3] - epsilon)


def _surface_levels(triangles):
    counts = {}
    for z, _, _ in triangles:
        key = round(z, 4)
        counts[key] = counts.get(key, 0) + 1
    return counts


def check_scene(scene, manifest) -> list[str]:
    """Return PASS/INFO/FAIL findings for geometry and demo playback checks.

    Obstacle and runway checks use descendant world-mesh vertices. Moving-flight
    broadphase uses cached root-local mesh bounds; narrowphase uses convex hulls
    in XY and actual Z intervals. A PASS here only establishes consistency of
    this illustrative scene and manifest.
    """
    findings = []

    def passed(message):
        findings.append("PASS: " + message)

    def failed(message):
        findings.append("FAIL: " + message)

    def info(message):
        findings.append("INFO: " + message)

    old_frame = scene.frame_current
    window = bpy.context.window
    old_scene = window.scene if window is not None else None
    try:
        if window is not None and window.scene != scene:
            window.scene = scene
        runways = manifest.get("runways", {})
        phases = manifest.get("demonstration_phases", [])
        if len(phases) != 3:
            failed(f"expected 3 demonstration phases, found {len(phases)}")
        for index, expected in enumerate(PHASE_FRAMES):
            if index >= len(phases):
                break
            phase = phases[index]
            actual = (int(phase.get("start_frame", -1)), int(phase.get("end_frame", -1)))
            if actual != expected:
                failed(f"phase {index + 1} frame range is {actual}; expected {expected}")
        if scene.frame_start != PHASE_FRAMES[0][0]:
            failed(f"scene starts at frame {scene.frame_start}; expected {PHASE_FRAMES[0][0]}")
        if scene.frame_end != PHASE_FRAMES[-1][1]:
            failed(f"scene ends at frame {scene.frame_end}; expected {PHASE_FRAMES[-1][1]}")
        scene_fps = scene.render.fps / scene.render.fps_base
        if abs(scene_fps - 60.0) > 1e-6:
            failed(f"scene frame rate is {scene_fps:g} fps; expected 60 fps")
        else:
            passed("native demonstration scene is authored at 60 fps")

        # Static obstacle geometry is measured from evaluated descendant meshes.
        scene.frame_set(1)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obstacle_bounds = {}
        obstacles = [obj for obj in scene.objects
                     if obj.get("obstacle_kind") in OBSTACLE_KINDS]
        for obstacle in obstacles:
            kind = str(obstacle.get("obstacle_kind"))
            vertices = _world_mesh_vertices(obstacle, depsgraph)
            bounds = _bounds_from_vertices(vertices)
            hull = _convex_hull_xy(vertices)
            if bounds is None or len(hull) < 3:
                failed(f"obstacle {obstacle.name!r} ({kind}) has no finite descendant mesh bounds")
                continue
            obstacle_bounds[obstacle.name] = (obstacle, bounds, hull)

        if not obstacles:
            failed("no semantic obstacle roots found (building/tree/parked_aircraft)")
        runway_specs = {}
        for key, spec in runways.items():
            root_name = spec.get("root")
            if not root_name or scene.objects.get(root_name) is None:
                failed(f"runway {key!r} root {root_name!r} is missing from the scene")
                continue
            try:
                runway_specs[key] = spec
                # Validate expected dimensions in display metres; no asset scale
                # is applied here because these manifest values already describe
                # the in-scene footprint.
                if float(spec["length"]) <= 0 or float(spec["width"]) <= 0:
                    failed(f"runway {key!r} has invalid length/width")
            except (KeyError, TypeError, ValueError) as exc:
                failed(f"runway {key!r} has incomplete geometry metadata: {exc}")

        min_runway_gap = (math.inf, None)
        runway_overlap_failures = 0
        for obstacle_name, (obstacle, bounds, hull) in obstacle_bounds.items():
            for key, spec in runway_specs.items():
                try:
                    gap = _runway_projection_gap(hull, spec)
                    if gap < min_runway_gap[0]:
                        min_runway_gap = (gap, (obstacle_name, key))
                    if gap <= 1e-6:
                        runway_overlap_failures += 1
                        failed(
                            f"obstacle {obstacle_name!r} ({obstacle.get('obstacle_kind')}) "
                            f"overlaps runway {key!r} expanded by {RUNWAY_CLEARANCE:.0f} display m"
                        )
                except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
                    failed(f"could not project obstacle {obstacle_name!r} against runway {key!r}: {exc}")
        if math.isfinite(min_runway_gap[0]):
            name, key = min_runway_gap[1]
            info(f"minimum obstacle-to-runway clearance beyond the {RUNWAY_CLEARANCE:.0f} m envelope: "
                 f"{min_runway_gap[0]:.2f} display m ({name} / {key})")
        if obstacles and len(obstacle_bounds) == len(obstacles) and runway_overlap_failures == 0:
            passed(f"{len(obstacle_bounds)} semantic obstacle roots clear all runway envelopes")

        # Compare the actual evaluated top triangles.  The apron and the
        # asphalt have the same nominal top elevation, so an XY overlap there
        # would recreate the visible Z-fighting this scene is meant to avoid.
        apron_root = scene.objects.get("Surface.TaxiApron")
        if apron_root is None:
            failed("Surface.TaxiApron root is missing")
        else:
            apron_triangles = _upward_planar_triangles(apron_root, depsgraph)
            runway_triangles = []
            for key, spec in runway_specs.items():
                runway_root = scene.objects.get(spec.get("root"))
                if runway_root is not None:
                    runway_triangles.extend(_upward_planar_triangles(runway_root, depsgraph))
            paint_root = scene.objects.get("Surface.TaxiPaint")
            paint_triangles = (_upward_planar_triangles(paint_root, depsgraph)
                               if paint_root is not None else [])
            if not apron_triangles:
                failed("Surface.TaxiApron has no upward-facing planar XY triangles")
            if not runway_triangles:
                failed("runway roots have no upward-facing planar XY triangles")
            apron_levels = _surface_levels(apron_triangles)
            runway_levels = _surface_levels(runway_triangles)
            paint_levels = _surface_levels(paint_triangles)
            if apron_triangles and runway_triangles:
                overlaps = []
                runway_index = []
                for z, triangle, obj_name in runway_triangles:
                    runway_index.append((z, triangle, _triangle_bounds_xy(triangle), obj_name))
                for apron_z, apron_triangle, apron_name in apron_triangles:
                    apron_bounds = _triangle_bounds_xy(apron_triangle)
                    for runway_z, runway_triangle, runway_bounds, runway_name in runway_index:
                        if abs(apron_z - runway_z) > 1e-4:
                            continue
                        if not _triangle_bounds_overlap(apron_bounds, runway_bounds):
                            continue
                        if _triangles_overlap_xy(apron_triangle, runway_triangle):
                            overlaps.append((apron_z, apron_name, runway_name))
                            if len(overlaps) >= 20:
                                break
                    if len(overlaps) >= 20:
                        break
                if overlaps:
                    for z, apron_name, runway_name in overlaps[:10]:
                        failed(f"same-height apron/runway top triangles overlap at z={z:.4f} "
                               f"({apron_name} / {runway_name})")
                    if len(overlaps) > 10:
                        failed(f"{len(overlaps) - 10} additional apron/runway top overlaps omitted")
                else:
                    passed(f"no positive-area same-height XY triangle overlap between apron and runway tops "
                           f"(apron {len(apron_triangles)} triangles; runway {len(runway_triangles)} triangles)")
            info(f"horizontal surface layers: apron z={sorted(apron_levels.items())}; "
                 f"taxi paint z={sorted(paint_levels.items())}; runway tops z={sorted(runway_levels.items())}")
            if apron_levels and paint_levels:
                apron_top = max(apron_levels)
                paint_top = min(paint_levels)
                info(f"measured taxi-paint/apron top separation: {paint_top - apron_top:.4f} display m "
                     f"(paint {paint_top:.4f}, apron {apron_top:.4f})")

        flights = {}
        for obj in scene.objects:
            role = obj.get("demo_role")
            if role in FLIGHT_ROLES:
                flights.setdefault(str(role), []).append(obj)
        for role in FLIGHT_ROLES:
            matches = flights.get(role, [])
            if len(matches) != 1:
                failed(f"expected exactly one moving root for {role!r}, found {len(matches)}")
        if len(flights) != len(FLIGHT_ROLES):
            extras = sorted(set(flights) - set(FLIGHT_ROLES))
            failed(f"unexpected moving-flight roles found: {extras}")

        state_objects = [obj for obj in scene.objects
                         if obj.type == "EMPTY" and obj.name.startswith("State.")]
        if len(state_objects) != 3:
            failed(f"expected 3 State.N overlay roots, found {len(state_objects)}")

        # Mesh-local corners are cached once. The aircraft geometry is rigid
        # relative to its moving root, so subsequent per-frame bounds need only
        # transform those corners by the evaluated root matrix.
        scene.frame_set(1)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        flight_local_corners = {}
        for role, roots in flights.items():
            if len(roots) != 1:
                continue
            corners = _local_bbox_corners(roots[0], depsgraph)
            if corners is None:
                failed(f"flight {role!r} has no finite mesh bounding box")
            else:
                flight_local_corners[role] = corners

        closed_phase = len(phases) >= 3 and not bool(phases[2].get("runway_18_usable", True))
        closed_phase_start = int(phases[2].get("start_frame", PHASE_FRAMES[2][0])) if len(phases) >= 3 else PHASE_FRAMES[2][0]
        min_aircraft_separation = (math.inf, None)
        min_obstacle_gap = (math.inf, None)
        collision_count = 0
        separation_failure_count = 0
        invalid_aircraft_frames = 0
        state_messages = []
        state_scale_failures = 0
        state_visibility_failures = 0
        west_spec = runway_specs.get("west")
        for frame in range(1, scene.frame_end + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            depsgraph = bpy.context.evaluated_depsgraph_get()

            active_states = []
            for obj in state_objects:
                scale = obj.evaluated_get(depsgraph).scale
                if not _finite_vector(scale):
                    state_scale_failures += 1
                    if len(state_messages) < 10:
                        state_messages.append(f"state root {obj.name!r} has a non-finite scale at frame {frame}")
                    continue
                components = tuple(float(value) for value in scale)
                if any(min(abs(value), abs(value - 1.0)) > 1e-4 for value in components):
                    state_scale_failures += 1
                    if len(state_messages) < 10:
                        state_messages.append(f"state root {obj.name!r} scale is not 0/1 at frame {frame}: {components}")
                if scale.x > 0.5:
                    active_states.append(obj.name)
            if len(active_states) != 1:
                state_visibility_failures += 1
                if len(state_messages) < 10:
                    state_messages.append(f"frame {frame}: expected exactly one active State.N root, found {active_states}")

            frame_centers = {}
            for role in FLIGHT_ROLES:
                roots = flights.get(role, [])
                if len(roots) != 1:
                    continue
                root = roots[0]
                evaluated_root = root.evaluated_get(depsgraph)
                location = evaluated_root.matrix_world.translation
                local_corners = flight_local_corners.get(role)
                world_corners = (_world_points_from_local_corners(evaluated_root.matrix_world, local_corners)
                                 if local_corners is not None else None)
                bounds = _bounds_from_points(world_corners) if world_corners is not None else None
                if not _finite_vector(location) or bounds is None:
                    invalid_aircraft_frames += 1
                    if invalid_aircraft_frames <= 10:
                        failed(f"flight {role!r} has non-finite transform/bounds at frame {frame}")
                    continue
                # The aircraft builders place their root origin at ground
                # center, so this is a stable, model-defined center point.
                frame_centers[role] = Vector(location)
                flight_hull = _convex_hull_xy(world_corners)

                hidden_parts = [part.name for part in _descendants(root)
                                if part.hide_render or part.hide_viewport]
                try:
                    hidden_parts.extend(part.name for part in _descendants(root) if part.hide_get())
                except RuntimeError:
                    pass
                if hidden_parts:
                    failed(f"flight {role!r} is hidden at frame {frame}: {sorted(set(hidden_parts))}")

                for obstacle_name, (_, obstacle_box, obstacle_hull) in obstacle_bounds.items():
                    vertical_overlap = (bounds[2][0] <= obstacle_box[2][1] and
                                        obstacle_box[2][0] <= bounds[2][1])
                    horizontal_overlap = _convex_polygons_overlap(flight_hull, obstacle_hull)
                    if vertical_overlap and horizontal_overlap:
                        collision_count += 1
                        if collision_count <= 20:
                            failed(f"flight {role!r} convex-hull/Z interval intersects obstacle {obstacle_name!r} "
                                   f"at frame {frame}")
                    horizontal_gap = _convex_polygon_distance(flight_hull, obstacle_hull)
                    vertical_gap = _interval_gap(bounds[2], obstacle_box[2])
                    gap = math.hypot(horizontal_gap, vertical_gap)
                    if gap < min_obstacle_gap[0]:
                        min_obstacle_gap = (gap, (role, obstacle_name, frame))

                # During the closed example the flexible departure must remain
                # away from the west runway while it is still on the ground.
                if (closed_phase and role == "depart_flex" and west_spec is not None and
                        frame >= closed_phase_start and
                        bounds[2][0] <= GROUND_HEIGHT_MAX and
                        _inside_expanded_runway(flight_hull, west_spec)):
                    failed(f"closed-phase depart_flex is on/near the west runway at frame {frame} "
                           f"while on the ground (z-min {bounds[2][0]:.2f})")

            roles = sorted(frame_centers)
            for first_index, first_role in enumerate(roles):
                for second_role in roles[first_index + 1:]:
                    distance = (frame_centers[first_role] - frame_centers[second_role]).length
                    if distance < min_aircraft_separation[0]:
                        min_aircraft_separation = (
                            distance, (first_role, second_role, frame)
                        )
                    if distance < AIRCRAFT_SEPARATION:
                        separation_failure_count += 1
                        if separation_failure_count <= 20:
                            failed(f"flight centers {first_role!r}/{second_role!r} are only "
                                   f"{distance:.2f} display m apart at frame {frame}; "
                                   f"minimum is {AIRCRAFT_SEPARATION:.0f} m")

        for message in state_messages:
            failed(message)
        if state_scale_failures > 10 or state_visibility_failures > 10:
            failed(f"additional state visibility/scale violations omitted: "
                   f"{max(0, state_scale_failures - 10)} scale, "
                   f"{max(0, state_visibility_failures - 10)} active-state")
        if state_scale_failures == 0 and state_visibility_failures == 0:
            passed(f"exactly one State.N overlay has scale 1 at every integer frame 1..{scene.frame_end}; others are 0")

        if invalid_aircraft_frames > 10:
            failed(f"{invalid_aircraft_frames - 10} additional invalid moving-flight samples omitted")
        if collision_count > 20:
            failed(f"{collision_count - 20} additional flight/obstacle hull intersections omitted")
        if separation_failure_count > 20:
            failed(f"{separation_failure_count - 20} additional aircraft-separation violations omitted")
        if math.isfinite(min_aircraft_separation[0]):
            first, second, frame = min_aircraft_separation[1]
            info(f"minimum moving-aircraft center separation: {min_aircraft_separation[0]:.2f} "
                 f"display m ({first} / {second}, frame {frame})")
            if min_aircraft_separation[0] >= AIRCRAFT_SEPARATION:
                passed(f"all visible moving-aircraft pairs stay at least {AIRCRAFT_SEPARATION:.0f} display m apart")
        if math.isfinite(min_obstacle_gap[0]):
            role, obstacle_name, frame = min_obstacle_gap[1]
            info(f"minimum moving-flight/obstacle hull/Z gap: {min_obstacle_gap[0]:.2f} display m "
                 f"({role} / {obstacle_name}, frame {frame})")
            if collision_count == 0:
                passed(f"moving-flight convex hulls/Z intervals do not intersect semantic obstacle hulls "
                       f"({scene.frame_end} integer frames)")

        # Check each route's last animation pose against its manifest target.
        endpoint_checks = 0
        endpoint_failures = 0
        timing_checks = 0
        timing_failures = 0
        for phase_index, phase in enumerate(phases):
            try:
                start = int(phase["start_frame"])
                end = int(phase["end_frame"])
            except (KeyError, TypeError, ValueError):
                continue
            paths = phase.get("paths", {})
            timing = phase.get("timing", {})
            for role in FLIGHT_ROLES:
                roots = flights.get(role, [])
                points = paths.get(role)
                role_timing = timing.get(role)
                if len(roots) != 1:
                    continue
                if not points:
                    failed(f"phase {phase_index + 1} has no manifest path for {role!r}")
                    continue
                path_valid = True
                for point_index, point in enumerate(points):
                    try:
                        coordinates = tuple(float(value) for value in point)
                    except (TypeError, ValueError):
                        coordinates = ()
                    if len(coordinates) != 3 or not all(math.isfinite(value) for value in coordinates):
                        failed(f"phase {phase_index + 1} path {role!r} point {point_index} is not a finite xyz triple")
                        path_valid = False
                        break
                if not path_valid:
                    continue
                if not isinstance(role_timing, dict):
                    timing_failures += 1
                    failed(f"phase {phase_index + 1} has no normalized timing for {role!r}")
                else:
                    try:
                        movement_start = float(role_timing["start"])
                        movement_finish = float(role_timing["finish"])
                        if not (0.0 <= movement_start < movement_finish <= 1.0):
                            timing_failures += 1
                            failed(f"phase {phase_index + 1} timing for {role!r} is outside normalized "
                                   f"0..1 or has no duration: {role_timing}")
                        else:
                            timing_checks += 1
                    except (KeyError, TypeError, ValueError):
                        timing_failures += 1
                        failed(f"phase {phase_index + 1} timing for {role!r} needs numeric start/finish")
                try:
                    target_values = tuple(float(value) for value in points[-1])
                    if len(target_values) != 3:
                        raise ValueError("expected x, y, z")
                    target = Vector(target_values)
                except (TypeError, ValueError, IndexError):
                    failed(f"phase {phase_index + 1} final path point for {role!r} is invalid")
                    continue
                scene.frame_set(end)
                bpy.context.view_layer.update()
                depsgraph = bpy.context.evaluated_depsgraph_get()
                actual = roots[0].evaluated_get(depsgraph).matrix_world.translation
                if not _finite_vector(actual):
                    failed(f"phase {phase_index + 1} flight {role!r} endpoint is non-finite")
                    continue
                endpoint_checks += 1
                error = (actual - target).length
                if error > 0.1:
                    endpoint_failures += 1
                    failed(f"phase {phase_index + 1} flight {role!r} ends {error:.3f} display m "
                           f"from its manifest target at frame {end}")
        if endpoint_failures == 0 and endpoint_checks == len(phases) * len(FLIGHT_ROLES) and len(phases) == 3:
            passed("all four aircraft roles reach each phase's manifest endpoint by its phase end")
        if timing_failures == 0 and timing_checks == len(phases) * len(FLIGHT_ROLES) and len(phases) == 3:
            passed("all route start/finish timings are normalized within 0..1")

        # The no-Runway-18 constraint applies only to the closed third example.
        if closed_phase:
            passed("closed phase is represented as a distinct manifest state")
        else:
            failed("the third demonstration phase must show Runway 18 closed")

    except Exception as exc:  # Keep the checker reportable from a batch verifier.
        failed(f"scene check could not complete: {type(exc).__name__}: {exc}")
    finally:
        try:
            scene.frame_set(old_frame)
            bpy.context.view_layer.update()
            if window is not None and old_scene is not None and window.scene != old_scene:
                window.scene = old_scene
        except Exception as exc:
            findings.append(f"INFO: could not restore Blender context after checking: {exc}")

    return findings
