"""Render the saved FRA demo playback as a low-cost, real-camera MP4 preview.

Usage from the repository root:

    blender --background assets/airport/fra-airport.blend \
      --python tools/blender/render_demo.py --

Render one actual scene frame without writing into the repository:

    blender --background assets/airport/fra-airport.blend \
      --python tools/blender/render_demo.py -- --smoke

The default video samples source frames 1, 3, ..., 1439.  At 12 fps this is
720 rendered frames and a 60-second playback of the 24 fps, 1440-frame scene.
The blend file is never saved or modified on disk.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import bpy


REPO_ROOT = Path(__file__).resolve().parents[2]
BLEND_PATH = REPO_ROOT / "assets" / "airport" / "fra-airport.blend"
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "airport" / "previews" / "airport-demo.mp4"
SMOKE_OUTPUT = Path("/tmp/fra-video-smoke.png")
TARGET_SCENE = "FRA · Airport demonstration"
VIDEO_FPS = 12
SAMPLE_STEP = 2
SAMPLES = 8
WIDTH = 960
HEIGHT = 660


def arguments():
    blender_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="render one real scene frame to /tmp")
    parser.add_argument("--frame", type=int, help="source frame for --smoke (defaults to saved current frame)")
    parser.add_argument("--smoke-output", type=Path, default=SMOKE_OUTPUT,
                        help=f"single-frame output path (default: {SMOKE_OUTPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"MP4 output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--width", type=int, default=WIDTH, help=f"render width (default: {WIDTH})")
    parser.add_argument("--height", type=int, default=HEIGHT, help=f"render height (default: {HEIGHT})")
    parser.add_argument("--samples", type=int, default=SAMPLES,
                        help=f"EEVEE temporal samples (default: {SAMPLES})")
    return parser.parse_args(blender_args)


def available_engines():
    try:
        prop = bpy.types.RenderSettings.bl_rna.properties["engine"]
        return {item.identifier for item in prop.enum_items}
    except Exception:
        return set()


def select_scene():
    scene = bpy.data.scenes.get(TARGET_SCENE)
    if scene is None:
        if not BLEND_PATH.exists():
            raise SystemExit(f"Saved Blender scene not found: {BLEND_PATH}")
        bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
        scene = bpy.data.scenes.get(TARGET_SCENE)
    if scene is None:
        raise SystemExit(f"Scene {TARGET_SCENE!r} is missing from {BLEND_PATH}")
    if scene.camera is None:
        raise SystemExit(f"Scene {TARGET_SCENE!r} has no active camera")
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    return scene


def set_common_render_settings(scene, width, height):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 10
    scene.render.film_transparent = False
    scene.render.use_file_extension = True


def set_eevee(scene, engine, samples):
    scene.render.engine = engine
    eevee = getattr(scene, "eevee", None)
    if eevee is not None and hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = samples


def set_workbench(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.background_type = "WORLD"
    if hasattr(scene.display, "render_aa"):
        scene.display.render_aa = "16"


def configure_engine(scene, samples):
    engines = available_engines()
    print(f"BLENDER_VERSION={bpy.app.version_string}", flush=True)
    print(f"AVAILABLE_RENDER_ENGINES={','.join(sorted(engines)) or 'unavailable'}", flush=True)
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if engine in engines:
            try:
                set_eevee(scene, engine, samples)
                return engine
            except Exception as exc:
                print(f"EEVEE_SETUP_FAILED={type(exc).__name__}: {exc}", flush=True)
    if "BLENDER_WORKBENCH" in engines:
        set_workbench(scene)
        print("RENDER_FALLBACK=Workbench material/studio shading (lower preview fidelity)", flush=True)
        return "BLENDER_WORKBENCH"
    raise SystemExit("Neither EEVEE nor Workbench is available in this Blender build")


def render_one(scene, source_frame, output_path):
    scene.frame_set(source_frame)
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def render_smoke(scene, engine, args):
    frame = args.frame if args.frame is not None else scene.frame_current
    if not scene.frame_start <= frame <= scene.frame_end:
        raise SystemExit(f"Smoke frame {frame} is outside {scene.frame_start}..{scene.frame_end}")
    args.smoke_output.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    try:
        render_one(scene, frame, args.smoke_output)
    except Exception as exc:
        if engine == "BLENDER_WORKBENCH" or "BLENDER_WORKBENCH" not in available_engines():
            raise
        print(f"EEVEE_HEADLESS_RENDER_FAILED={type(exc).__name__}: {exc}", flush=True)
        set_workbench(scene)
        print("RENDER_FALLBACK=Workbench material/studio shading (lower preview fidelity)", flush=True)
        render_one(scene, frame, args.smoke_output)
        engine = "BLENDER_WORKBENCH"
    elapsed = time.monotonic() - start
    print(f"SMOKE_ENGINE={engine}", flush=True)
    print(f"SMOKE_SOURCE_FRAME={frame}", flush=True)
    print(f"SMOKE_OUTPUT={args.smoke_output}", flush=True)
    print(f"SMOKE_SECONDS={elapsed:.2f}", flush=True)


def ffmpeg_path():
    candidate = shutil.which("ffmpeg")
    if candidate:
        return candidate
    for path in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if Path(path).is_file() and Path(path).stat().st_mode & 0o111:
            return path
    return None


def render_sequence(scene, engine, args, encoder):
    frames = list(range(scene.frame_start, scene.frame_end + 1, SAMPLE_STEP))
    expected_frames = (scene.frame_end - scene.frame_start) // SAMPLE_STEP + 1
    if len(frames) != expected_frames or len(frames) != 720:
        raise SystemExit(f"Expected 720 samples from frames 1,3,...,1439; got {len(frames)} "
                         f"from scene range {scene.frame_start}..{scene.frame_end}")
    duration = len(frames) / VIDEO_FPS
    if abs(duration - 60.0) > 1e-9:
        raise SystemExit(f"Expected a 60-second video at {VIDEO_FPS} fps; got {duration:.3f}s")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="fra-airport-demo-") as temp_dir:
        frames_dir = Path(temp_dir)

        def render_all():
            for index, source_frame in enumerate(frames, start=1):
                destination = frames_dir / f"frame_{index:06d}.png"
                render_one(scene, source_frame, destination)
                if index == 1 or index % 60 == 0 or index == len(frames):
                    print(f"RENDER_PROGRESS={index}/{len(frames)} source_frame={source_frame}", flush=True)

        try:
            render_all()
        except Exception as exc:
            if engine == "BLENDER_WORKBENCH" or "BLENDER_WORKBENCH" not in available_engines():
                raise
            print(f"EEVEE_SEQUENCE_FAILED={type(exc).__name__}: {exc}; restarting with Workbench", flush=True)
            for frame_file in frames_dir.glob("frame_*.png"):
                frame_file.unlink()
            set_workbench(scene)
            engine = "BLENDER_WORKBENCH"
            print("RENDER_FALLBACK=Workbench material/studio shading (lower preview fidelity)", flush=True)
            render_all()

        command = [
            encoder, "-hide_banner", "-loglevel", "warning", "-y",
            "-framerate", str(VIDEO_FPS), "-start_number", "1",
            "-i", str(frames_dir / "frame_%06d.png"),
            "-frames:v", str(len(frames)),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(args.output),
        ]
        subprocess.run(command, check=True)

    elapsed = time.monotonic() - started
    print(f"VIDEO_ENGINE={engine}", flush=True)
    print(f"VIDEO_SOURCE_FRAMES={frames[0]}..{frames[-1]} step {SAMPLE_STEP}", flush=True)
    print(f"VIDEO_FRAMES={len(frames)}", flush=True)
    print(f"VIDEO_FPS={VIDEO_FPS}", flush=True)
    print(f"VIDEO_DURATION_SECONDS={duration:.2f}", flush=True)
    print(f"VIDEO_OUTPUT={args.output}", flush=True)
    print(f"VIDEO_SECONDS={elapsed:.2f}", flush=True)


def main():
    args = arguments()
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("Render dimensions must be positive")
    if args.samples <= 0:
        raise SystemExit("EEVEE sample count must be positive")
    scene = select_scene()
    set_common_render_settings(scene, args.width, args.height)
    engine = configure_engine(scene, args.samples)
    if args.smoke:
        render_smoke(scene, engine, args)
        return
    encoder = ffmpeg_path()
    if encoder is None:
        raise SystemExit("ffmpeg is not available on PATH or in /opt/homebrew/bin /usr/local/bin")
    print(f"FFMPEG={encoder}", flush=True)
    render_sequence(scene, engine, args, encoder)


if __name__ == "__main__":
    main()
