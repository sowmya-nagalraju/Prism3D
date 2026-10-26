"""
Prism3D - Image to 3D Conversion Engine
Core module for transforming 2D images (drawings, photos, blueprints, anime, cartoons)
into smooth, colored, 3D-printable watertight meshes.
"""

from .depth_engine import generate_depth_map, preprocess_image, ConversionMode
from .mesh_builder import build_colored_3d_mesh
from .exporter import export_model

__all__ = [
    "generate_depth_map",
    "preprocess_image",
    "ConversionMode",
    "build_colored_3d_mesh",
    "export_model"
]
