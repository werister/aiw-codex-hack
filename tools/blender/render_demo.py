"""Render the saved FRA demo playback as a high-frame-rate, real-camera MP4.

Usage from the repository root:

    blender --background assets/airport/fra-airport.blend \
      --python tools/blender/render_demo.py --

Render one actual scene frame without writing into the repository:

    blender --background assets/airport/fra-airport.blend \
      --python tools/blender/render_demo.py -- --smoke

The output is 60 fps for 60 seconds. A 24 fps source is rendered at actual
subframe times; a 60 fps native scene renders every frame. EEVEE renders at
1280x880 with 32 temporal samples. No optical-flow interpolation is used. The
blend file is never saved or modified on disk.
"""

from __future__ import annotations

import argparse
import math
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
VIDEO_FPS = 60
SAMPLES = 32
WIDTH = 1280
HEIGHT = 880
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 880


def arguments():
    blender_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="render one real scene frame to /tmp")
    parser.add_argument("--benchmark", action="store_true",
                        help="render three consecutive samples in one process to /tmp")
    parser.add_argument("--benchmark-frames", type=int, default=3,
                        help="sample count for --benchmark (default: 3)")
    parser.add_argument("--workbench", action="store_true",
                        help="force Workbench material/studio shading for engine comparisons")
    parser.add_argument("--frame", type=int, help="source start frame for --smoke/--benchmark")
    parser.add_argument("--smoke-output", type=Path, default=SMOKE_OUTPUT,
                        help=f"single-frame output path (default: {SMOKE_OUTPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"MP4 output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--width", type=int, default=WIDTH, help=f"render width (default: {WIDTH})")
    parser.add_argument("--height", type=int, default=HEIGHT, help=f"render height (default: {HEIGHT})")
    parser.add_argument("--output-width", type=int, default=OUTPUT_WIDTH,
                        help=f"downsampled MP4 width (default: {OUTPUT_WIDTH})")
    parser.add_argument("--output-height", type=int, default=OUTPUT_HEIGHT,
                        help=f"downsampled MP4 height (default: {OUTPUT_HEIGHT})")
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
    scene.render.image_settings.compression = 0
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
    shading.cavity_type = "WORLD"
    shading.background_type = "WORLD"
    if hasattr(shading, "show_object_outline"):
        shading.show_object_outline = False
    if hasattr(shading, "show_outline_selected"):
        shading.show_outline_selected = False
    if hasattr(scene.display, "render_aa"):
        scene.display.render_aa = "32"


def configure_engine(scene, samples, force_workbench=False):
    engines = available_engines()
    print(f"BLENDER_VERSION={bpy.app.version_string}", flush=True)
    print(f"AVAILABLE_RENDER_ENGINES={','.join(sorted(engines)) or 'unavailable'}", flush=True)
    if force_workbench:
        try:
            set_workbench(scene)
        except Exception as exc:
            raise SystemExit(f"Workbench is not available in this Blender build: {exc}")
        print("RENDER_ENGINE=Workbench material/studio shading (lower preview fidelity)", flush=True)
        return "BLENDER_WORKBENCH"
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
    whole_frame = math.floor(source_frame)
    scene.frame_set(whole_frame, subframe=source_frame - whole_frame)
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


def render_benchmark(scene, engine, args):
    start_frame = float(args.frame if args.frame is not None else scene.frame_current)
    source_fps = scene.render.fps / scene.render.fps_base
    sample_step = source_fps / VIDEO_FPS
    frames = [start_frame + sample_step * index for index in range(args.benchmark_frames)]
    if frames[0] < scene.frame_start or frames[-1] > scene.frame_end:
        raise SystemExit(f"Benchmark frames {frames[0]}..{frames[-1]} are outside "
                         f"{scene.frame_start}..{scene.frame_end}")
    output_dir = Path("/tmp/fra-video-benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    durations = []
    for index, source_frame in enumerate(frames):
        destination = output_dir / f"fra-bench-{index:03d}.png"
        started = time.monotonic()
        try:
            render_one(scene, source_frame, destination)
        except Exception as exc:
            if engine == "BLENDER_WORKBENCH" or "BLENDER_WORKBENCH" not in available_engines():
                raise
            print(f"EEVEE_HEADLESS_RENDER_FAILED={type(exc).__name__}: {exc}", flush=True)
            set_workbench(scene)
            engine = "BLENDER_WORKBENCH"
            print("RENDER_FALLBACK=Workbench material/studio shading (lower preview fidelity)", flush=True)
            render_one(scene, source_frame, destination)
        elapsed = time.monotonic() - started
        durations.append(elapsed)
        print(f"BENCHMARK_FRAME={source_frame:.3f} SECONDS={elapsed:.2f} ENGINE={engine}", flush=True)
    print(f"BENCHMARK_ENGINE={engine}", flush=True)
    print(f"BENCHMARK_SOURCE_FPS={source_fps:g}", flush=True)
    print(f"BENCHMARK_FRAMES={','.join(f'{frame:.3f}' for frame in frames)}", flush=True)
    print(f"BENCHMARK_AVERAGE_SECONDS={sum(durations) / len(durations):.2f}", flush=True)
    print(f"BENCHMARK_OUTPUT_DIR={output_dir}", flush=True)


def ffmpeg_path():
    candidate = shutil.which("ffmpeg")
    if candidate:
        return candidate
    for path in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if Path(path).is_file() and Path(path).stat().st_mode & 0o111:
            return path
    return None


def render_sequence(scene, engine, args, encoder):
    source_fps = scene.render.fps / scene.render.fps_base
    duration = (scene.frame_end - scene.frame_start + 1) / source_fps
    output_frames = round(duration * VIDEO_FPS)
    if abs(duration - 60.0) > 1e-6 or output_frames != 3600:
        raise SystemExit(f"Expected a 60-second scene and 3,600 output frames; "
                         f"scene is {duration:.3f}s ({scene.frame_start}..{scene.frame_end} at {source_fps:g} fps)")
    sample_step = source_fps / VIDEO_FPS
    frames = [scene.frame_start + index * sample_step for index in range(output_frames)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="fra-airport-demo-") as temp_dir:
        frames_dir = Path(temp_dir)

        def render_all():
            for index, source_frame in enumerate(frames, start=1):
                destination = frames_dir / f"frame_{index:06d}.png"
                render_one(scene, source_frame, destination)
                if index == 1 or index % 120 == 0 or index == len(frames):
                    print(f"RENDER_PROGRESS={index}/{len(frames)} source_frame={source_frame:.3f}", flush=True)

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

        temporary_output = frames_dir / "airport-demo.mp4"
        command = [
            encoder, "-hide_banner", "-loglevel", "warning", "-y",
            "-framerate", str(VIDEO_FPS), "-start_number", "1",
            "-i", str(frames_dir / "frame_%06d.png"),
            "-frames:v", str(len(frames)),
            "-vf", f"scale={args.output_width}:{args.output_height}:flags=lanczos",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(temporary_output),
        ]
        subprocess.run(command, check=True)
        shutil.move(str(temporary_output), str(args.output))

    elapsed = time.monotonic() - started
    print(f"VIDEO_ENGINE={engine}", flush=True)
    print(f"VIDEO_SOURCE_FPS={source_fps:g}", flush=True)
    print(f"VIDEO_SOURCE_FRAMES={frames[0]:.3f}..{frames[-1]:.3f} step {sample_step:.6f}", flush=True)
    print(f"VIDEO_FRAMES={len(frames)}", flush=True)
    print(f"VIDEO_FPS={VIDEO_FPS}", flush=True)
    print(f"VIDEO_DURATION_SECONDS={duration:.2f}", flush=True)
    print(f"VIDEO_RENDER_SIZE={args.width}x{args.height}", flush=True)
    print(f"VIDEO_OUTPUT_SIZE={args.output_width}x{args.output_height}", flush=True)
    print(f"VIDEO_OUTPUT={args.output}", flush=True)
    print(f"VIDEO_SECONDS={elapsed:.2f}", flush=True)


def main():
    args = arguments()
    if args.smoke and args.benchmark:
        raise SystemExit("Choose either --smoke or --benchmark")
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("Render dimensions must be positive")
    if args.output_width <= 0 or args.output_height <= 0:
        raise SystemExit("Output video dimensions must be positive")
    if args.output_width > args.width or args.output_height > args.height:
        raise SystemExit("Output dimensions must not exceed the supersampled render dimensions")
    if args.samples <= 0:
        raise SystemExit("EEVEE sample count must be positive")
    if args.benchmark_frames <= 0:
        raise SystemExit("Benchmark frame count must be positive")
    scene = select_scene()
    set_common_render_settings(scene, args.width, args.height)
    engine = configure_engine(scene, args.samples, args.workbench)
    if args.benchmark:
        render_benchmark(scene, engine, args)
        return
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
