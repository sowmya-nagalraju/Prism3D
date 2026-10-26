"""
Prism3D Web Application Server
FastAPI backend providing real-time 2D-to-3D conversion endpoints,
live model streaming, and multi-format exports (STL, GLB, OBJ, PLY).
"""

import os
import shutil
import uuid
import io
import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import uvicorn

from converter.depth_engine import generate_depth_map, preprocess_image, ConversionMode
from converter.mesh_builder import build_colored_3d_mesh
from converter.exporter import export_model

app = FastAPI(title="Prism3D - Image to 3D Studio", version="1.0.0")

# Enable CORS for local development and embedded webviews
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CACHE_DIR = BASE_DIR / "temp_models"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory session store for active models
ACTIVE_MODELS = {}


@app.get("/api/samples")
async def get_samples():
    """Returns the list of built-in sample images and presets."""
    samples = [
        {
            "id": "anime",
            "name": "Anime Chibi Figurine",
            "category": "Anime & Cartoon",
            "image": "/static/samples/anime_character.png",
            "mode": "anime_cartoon",
            "width": 100,
            "height": 16,
            "base": 3,
            "smoothness": 1.2,
            "description": "Transforms 2D anime character drawings into rounded, smooth 3D figurine shapes with vibrant hair and colors."
        },
        {
            "id": "blueprint",
            "name": "Architectural Floor Plan",
            "category": "Blueprint & Schematic",
            "image": "/static/samples/architectural_blueprint.png",
            "mode": "blueprint",
            "width": 120,
            "height": 10,
            "base": 2,
            "smoothness": 0.5,
            "description": "Auto-detects blueprint walls and technical line drawings, extruding them into solid architectural models."
        },
        {
            "id": "sketch",
            "name": "Artistic Pencil Mandala",
            "category": "Drawing & Sketch",
            "image": "/static/samples/pencil_sketch.png",
            "mode": "sketch_lineart",
            "width": 90,
            "height": 8,
            "base": 3,
            "smoothness": 1.0,
            "description": "Converts graphite pencil strokes and ink drawings into smooth tactile embossed 3D relief carvings."
        },
        {
            "id": "photo",
            "name": "Vibrant Flora Relief",
            "category": "Photo & Bas-Relief",
            "image": "/static/samples/vibrant_photo.png",
            "mode": "photo_relief",
            "width": 100,
            "height": 14,
            "base": 3,
            "smoothness": 1.0,
            "description": "Multi-scale depth estimation that turns photos and continuous-tone art into smooth bas-relief sculpture."
        }
    ]
    return JSONResponse(samples)


@app.post("/api/convert")
async def convert_image_to_3d(
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    sample_id: Optional[str] = Form(None),
    mode: str = Form("photo_relief"),
    width_mm: float = Form(100.0),
    max_height_mm: float = Form(12.0),
    base_thickness_mm: float = Form(3.0),
    smoothness: float = Form(1.0),
    resolution: int = Form(256),
    invert: bool = Form(False),
    dual_sided: bool = Form(False),
    curve_arc_deg: float = Form(0.0)
):
    """
    Main conversion endpoint: accepts an uploaded image file, base64 image data, or a sample ID,
    runs the specialized depth and mesh pipeline, and stores the resulting model.
    """
    try:
        # Normalize form values in case invoked directly
        def _get(val, default):
            if hasattr(val, "default"):
                return val.default
            return default if val is None else val

        mode = str(_get(mode, "photo_relief"))
        width_mm = float(_get(width_mm, 100.0))
        max_height_mm = float(_get(max_height_mm, 12.0))
        base_thickness_mm = float(_get(base_thickness_mm, 3.0))
        smoothness = float(_get(smoothness, 1.0))
        resolution = int(_get(resolution, 256))
        invert = bool(_get(invert, False))
        dual_sided = bool(_get(dual_sided, False))
        curve_arc_deg = float(_get(curve_arc_deg, 0.0))

        image = None

        # 1. Try uploaded file (duck-typed for any Starlette / FastAPI UploadFile or file-like object)
        if file is not None and hasattr(file, "file"):
            try:
                image = Image.open(file.file)
            except Exception as e:
                print("Failed to open file.file:", e)

        # 2. Try base64 image data (completely bypasses multipart boundary quirks)
        if image is None and image_base64 and not hasattr(image_base64, "default"):
            b64_str = str(image_base64).strip()
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(b64_str)
                image = Image.open(io.BytesIO(raw_bytes))
            except Exception as e:
                print("Failed to decode base64 image:", e)

        # 3. Try sample preset ID
        if image is None and sample_id and not hasattr(sample_id, "default"):
            s_id = str(sample_id).strip()
            sample_map = {
                "anime": "anime_character.png",
                "blueprint": "architectural_blueprint.png",
                "sketch": "pencil_sketch.png",
                "photo": "vibrant_photo.png"
            }
            if s_id in sample_map:
                sample_path = STATIC_DIR / "samples" / sample_map[s_id]
                if sample_path.exists():
                    image = Image.open(sample_path)

        if image is None:
            raise HTTPException(status_code=400, detail="No image file or sample provided. Please upload an image.")

        # Clamp resolution for web responsiveness
        res = max(64, min(resolution, 512))

        # 1. Preprocess image
        rgb, alpha = preprocess_image(image, max_dim=res)

        # 2. Extract Depth
        depth = generate_depth_map(
            rgb=rgb,
            alpha=alpha,
            mode=mode,
            smoothness=smoothness,
            invert=invert
        )

        # 3. Construct Watertight Colored 3D Mesh
        mesh = build_colored_3d_mesh(
            depth_map=depth,
            rgb_image=rgb,
            width_mm=width_mm,
            max_height_mm=max_height_mm,
            base_thickness_mm=base_thickness_mm,
            dual_sided=dual_sided,
            curve_arc_deg=curve_arc_deg,
            mesh_resolution=res
        )

        # Generate unique model ID
        model_id = str(uuid.uuid4())
        model_dir = CACHE_DIR / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save GLB for web 3D viewer
        glb_path = model_dir / "model.glb"
        export_model(mesh, glb_path, file_format="glb")

        # Cache mesh in memory for fast on-demand format export
        ACTIVE_MODELS[model_id] = {
            "mesh": mesh,
            "dir": model_dir
        }

        # Calculate bounding dimensions and volume
        bounds = mesh.bounding_box.extents
        dim_x = round(float(bounds[0]), 1)
        dim_y = round(float(bounds[1]), 1)
        dim_z = round(float(bounds[2]), 1)
        
        # Calculate approximate volume in cm³ (mesh units are mm, so divide by 1000)
        volume_cm3 = round(abs(float(mesh.volume)) / 1000.0, 2) if mesh.is_watertight else 0.0

        return JSONResponse({
            "success": True,
            "model_id": model_id,
            "glb_url": f"/api/models/{model_id}/glb",
            "stats": {
                "vertices": int(len(mesh.vertices)),
                "triangles": int(len(mesh.faces)),
                "watertight": bool(mesh.is_watertight),
                "width_mm": dim_x,
                "length_mm": dim_y,
                "height_mm": dim_z,
                "volume_cm3": volume_cm3
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_id}/glb")
async def get_model_glb(model_id: str):
    """Streams the GLB model to the Three.js web viewer."""
    glb_path = CACHE_DIR / model_id / "model.glb"
    if not glb_path.exists():
        raise HTTPException(status_code=404, detail="Model GLB not found")
    return FileResponse(glb_path, media_type="model/gltf-binary")


@app.get("/api/download/{model_id}/{file_format}")
async def download_model(model_id: str, file_format: str):
    """
    Exports and streams the model in the requested format (stl, glb, obj, ply).
    """
    file_format = file_format.lower()
    if file_format not in ("stl", "glb", "obj", "ply"):
        raise HTTPException(status_code=400, detail="Invalid format. Supported: stl, glb, obj, ply")

    model_dir = CACHE_DIR / model_id
    out_file = model_dir / f"prism3d_model.{file_format}"

    if out_file.exists():
        return FileResponse(
            out_file,
            filename=f"prism3d_model_{model_id[:6]}.{file_format}",
            media_type="application/octet-stream"
        )

    # Check memory cache to export
    if model_id in ACTIVE_MODELS:
        mesh = ACTIVE_MODELS[model_id]["mesh"]
        export_model(mesh, out_file, file_format=file_format)
        return FileResponse(
            out_file,
            filename=f"prism3d_model_{model_id[:6]}.{file_format}",
            media_type="application/octet-stream"
        )

    raise HTTPException(status_code=404, detail="Model not found")


@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")

# Mount static web directory at both /static and root for complete URL compatibility
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root_static")


def start():
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start()
