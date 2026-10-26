"""
Prism3D - Command Line Interface
Convert any 2D image (drawing, blueprint, anime, cartoon, photo) into 3D printable models.

Usage:
    python convert_cli.py input.png output.stl
    python convert_cli.py character.png model.glb --mode anime_cartoon --height 15
    python convert_cli.py floorplan.png walls.stl --mode blueprint --width 150 --base 4
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

from converter.depth_engine import generate_depth_map, preprocess_image, ConversionMode
from converter.mesh_builder import build_colored_3d_mesh
from converter.exporter import export_model


def main():
    parser = argparse.ArgumentParser(
        description="Prism3D: Convert drawings, photos, blueprints & anime art into smooth colored 3D printable models."
    )
    parser.add_argument("input_image", type=str, help="Path to input 2D image (PNG, JPG, WEBP, BMP)")
    parser.add_argument("output_model", type=str, help="Path to output 3D file (.stl, .glb, .obj, .ply)")
    parser.add_argument(
        "--mode",
        type=str,
        default="photo_relief",
        choices=["anime_cartoon", "photo_relief", "blueprint", "sketch_lineart", "lithophane"],
        help="Conversion algorithm profile"
    )
    parser.add_argument("--width", type=float, default=100.0, help="Target 3D width in millimeters (default: 100mm)")
    parser.add_argument("--height", type=float, default=12.0, help="Max relief height/depth in millimeters (default: 12mm)")
    parser.add_argument("--base", type=float, default=3.0, help="Solid base thickness in millimeters (default: 3mm)")
    parser.add_argument("--smoothness", type=float, default=1.0, help="Surface smoothing factor (0.1 to 5.0, default: 1.0)")
    parser.add_argument("--resolution", type=int, default=256, help="Grid mesh resolution (e.g. 128, 256, 512, default: 256)")
    parser.add_argument("--invert", action="store_true", help="Invert depth / relief elevation")
    parser.add_argument("--dual-sided", action="store_true", help="Mirror front and back for standalone figurine")
    parser.add_argument("--curve", type=float, default=0.0, help="Cylindrical arc curve in degrees (e.g. 45-120 for lithophanes)")

    args = parser.parse_args()

    input_path = Path(args.input_image)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output_model)
    ext = output_path.suffix.lower().lstrip(".")
    if ext not in ("stl", "glb", "obj", "ply"):
        print(f"Warning: Extension '{ext}' unrecognized, defaulting to STL.", file=sys.stderr)
        ext = "stl"

    print(f"--> Loading image: {input_path}")
    image = Image.open(input_path)

    print(f"--> Preprocessing (resolution grid: {args.resolution})...")
    rgb, alpha = preprocess_image(image, max_dim=args.resolution)

    print(f"--> Generating depth map using mode '{args.mode}' (smoothness={args.smoothness})...")
    depth = generate_depth_map(rgb, alpha, mode=args.mode, smoothness=args.smoothness, invert=args.invert)

    print(f"--> Constructing watertight 3D mesh (width={args.width}mm, height={args.height}mm, base={args.base}mm)...")
    mesh = build_colored_3d_mesh(
        depth_map=depth,
        rgb_image=rgb,
        width_mm=args.width,
        max_height_mm=args.height,
        base_thickness_mm=args.base,
        dual_sided=args.dual_sided,
        curve_arc_deg=args.curve,
        mesh_resolution=args.resolution
    )

    print(f"    Mesh stats: {len(mesh.vertices):,} vertices, {len(mesh.faces):,} triangles | Watertight: {mesh.is_watertight}")

    print(f"--> Exporting to {output_path} ({ext.upper()})...")
    export_model(mesh, output_path, file_format=ext)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"--> Success! 3D model created: {output_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
