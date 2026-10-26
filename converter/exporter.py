"""
3D Model Exporter
Exports 3D meshes into STL, GLB, OBJ+MTL, and PLY formats with vertex colors and manifold geometry.
"""

from pathlib import Path
import numpy as np
import trimesh


def export_model(mesh: trimesh.Trimesh, output_path: str | Path, file_format: str = "stl") -> bytes:
    """
    Exports a trimesh.Trimesh object to the specified format.
    
    Supported formats:
        - "stl": Binary STL (Standard for all 3D printers and slicers)
        - "glb": Binary glTF 2.0 (Full embedded color & material, for 3D viewers)
        - "obj": Wavefront OBJ with vertex colors and material
        - "ply": Stanford Polygon File with per-vertex RGB colors
    """
    file_format = file_format.lower().strip()
    path = Path(output_path) if output_path else None

    if file_format == "stl":
        # Binary STL export for 3D printing
        data = mesh.export(file_type="stl")
        if isinstance(data, str):
            data = data.encode("utf-8")
        if path:
            with open(path, "wb") as f:
                f.write(data)
        return data

    elif file_format == "glb":
        # Binary glTF 2.0 export with colors
        data = mesh.export(file_type="glb")
        if path:
            with open(path, "wb") as f:
                f.write(data)
        return data

    elif file_format == "ply":
        # PLY format with per-vertex colors
        data = mesh.export(file_type="ply", encoding="binary")
        if isinstance(data, str):
            data = data.encode("utf-8")
        if path:
            with open(path, "wb") as f:
                f.write(data)
        return data

    elif file_format == "obj":
        # Standard OBJ format
        # If writing to a file, also generate accompanied .mtl if needed
        data = mesh.export(file_type="obj")
        if isinstance(data, str):
            data = data.encode("utf-8")
        if path:
            with open(path, "wb") as f:
                f.write(data)
        return data

    else:
        raise ValueError(f"Unsupported export format: {file_format}. Supported: stl, glb, obj, ply")
