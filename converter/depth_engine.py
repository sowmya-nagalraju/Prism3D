"""
Depth and Elevation Extraction Engine
Supports photos, blueprints, anime/cartoons, sketches, and lithophanes.
"""

from enum import Enum
import numpy as np
from PIL import Image
from scipy.ndimage import (
    gaussian_filter,
    distance_transform_edt,
    binary_fill_holes,
    binary_closing,
    generate_binary_structure
)


class ConversionMode(str, Enum):
    ANIME_CARTOON = "anime_cartoon"      # Organic figurine inflation with smooth dome curves
    PHOTO_RELIEF = "photo_relief"        # Multi-scale bas-relief with edge-preserving smoothing
    BLUEPRINT = "blueprint"              # Sharp structural extrusion of walls/lines on solid base
    SKETCH_LINEART = "sketch_lineart"    # Embossed/engraved line art with tactile rounded ridges
    LITHOPHANE = "lithophane"            # Inverse optical density for translucent backlit printing


def preprocess_image(image: Image.Image, max_dim: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """
    Resizes image preserving aspect ratio to max_dim, returns (rgb_array, alpha_array_or_none).
    Image colors are normalized to [0, 255] uint8.
    """
    w, h = image.size
    scale = min(max_dim / max(w, h), 1.0)
    if scale < 1.0:
        new_w = max(16, int(round(w * scale)))
        new_h = max(16, int(round(h * scale)))
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Ensure RGB / RGBA
    if image.mode in ("RGBA", "LA"):
        rgba = image.convert("RGBA")
        rgb = np.array(rgba)[:, :, :3]
        alpha = np.array(rgba)[:, :, 3]
    else:
        rgb = np.array(image.convert("RGB"))
        alpha = None

    return rgb, alpha


def _get_perceptual_luminance(rgb: np.ndarray) -> np.ndarray:
    """Calculates ITU-R BT.709 relative luminance."""
    return (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]) / 255.0


def _compute_anime_cartoon_depth(rgb: np.ndarray, alpha: np.ndarray | None, smoothness: float) -> np.ndarray:
    """
    Inflates 2D anime/cartoon characters into smooth 3D rounded figurine shapes.
    Uses Euclidean distance transform + curvature dome shaping + color luminance details.
    """
    h, w, _ = rgb.shape
    lum = _get_perceptual_luminance(rgb)

    # 1. Determine Foreground Mask
    if alpha is not None and np.any(alpha < 240):
        # Alpha channel provided (transparent background)
        fg_mask = alpha > 40
    else:
        # Detect background by sampling border pixels
        border_pixels = np.concatenate([
            rgb[0, :, :], rgb[-1, :, :],
            rgb[:, 0, :], rgb[:, -1, :]
        ], axis=0).astype(np.float32)
        bg_color = np.median(border_pixels, axis=0)
        
        # Color distance from estimated background
        color_diff = np.linalg.norm(rgb.astype(np.float32) - bg_color, axis=2)
        
        # Threshold to separate foreground character from background
        threshold = max(25.0, np.percentile(color_diff, 18))
        fg_mask = color_diff > threshold
        
        # Clean up mask (fill internal holes, e.g. character's shirt, eyes, hair)
        fg_mask = binary_fill_holes(fg_mask)
        struct = generate_binary_structure(2, 2)
        fg_mask = binary_closing(fg_mask, structure=struct, iterations=2)
    
    # 2. Euclidean Distance Transform for volumetric inflation
    if np.any(fg_mask):
        dist = distance_transform_edt(fg_mask)
        max_dist = dist.max()
        if max_dist > 0:
            dist_norm = dist / max_dist
        else:
            dist_norm = dist
        
        # Spherical / harmonic dome curve: sqrt(1 - (1 - d)^2) produces a smooth, rounded toy puffiness
        dome = np.sqrt(np.clip(1.0 - (1.0 - dist_norm) ** 2, 0.0, 1.0))
    else:
        dome = lum

    # 3. Add surface relief from clothing/hair/facial features
    # Subtract low-frequency luminance to isolate detailed features
    sigma_base = max(1.0, 4.0 * smoothness)
    lum_blur = gaussian_filter(lum, sigma=sigma_base)
    features = lum - lum_blur
    
    # Combine volumetric dome inflation (75%) with surface detail (25%)
    combined = 0.75 * dome + 0.25 * (features * 0.8 + 0.5) * (dome > 0.05)
    
    # Apply user smoothness
    final_depth = gaussian_filter(combined, sigma=max(0.5, smoothness * 1.5))
    
    # Normalize to [0, 1]
    denom = final_depth.max() - final_depth.min()
    if denom > 1e-6:
        final_depth = (final_depth - final_depth.min()) / denom
    else:
        final_depth = np.zeros_like(final_depth)
        
    return final_depth


def _compute_blueprint_depth(rgb: np.ndarray, smoothness: float) -> np.ndarray:
    """
    Transforms CAD schematics and architectural blueprints into solid extruded 3D models.
    Detects lines/walls and generates sharp, solid structural height with smooth top bevels.
    """
    lum = _get_perceptual_luminance(rgb)
    
    # Check if image is typical cyan/blue blueprint (high blue/cyan channel, low red)
    r = rgb[:, :, 0].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    is_cyan_blueprint = np.mean(b) > (np.mean(r) + 20)
    
    if is_cyan_blueprint:
        # Blueprint with white/cyan lines on deep blue background
        # Lines are brighter than background
        local_mean = gaussian_filter(lum, sigma=15)
        lines_mask = lum > (local_mean + 0.08)
    else:
        # Standard white/light background with dark lines or vice versa
        # Check median luminance
        if np.median(lum) > 0.5:
            # White background with dark lines (standard floor plan / sketch)
            local_mean = gaussian_filter(lum, sigma=15)
            lines_mask = lum < (local_mean - 0.08)
        else:
            # Dark background with light lines
            local_mean = gaussian_filter(lum, sigma=15)
            lines_mask = lum > (local_mean + 0.08)

    # Clean lines and fill gaps
    struct = generate_binary_structure(2, 1)
    cleaned = binary_closing(lines_mask, structure=struct, iterations=1)
    
    # Distance transform on walls to create subtle chamfer/bevel so 3D print overhangs are clean
    dist = distance_transform_edt(cleaned)
    max_d = dist.max()
    if max_d > 0:
        height = np.clip(dist / min(max_d, 3.5), 0.0, 1.0)
    else:
        height = cleaned.astype(np.float32)

    # Apply slight smoothing for print quality
    if smoothness > 0.1:
        height = gaussian_filter(height, sigma=smoothness * 0.8)

    return height


def _compute_photo_relief_depth(rgb: np.ndarray, smoothness: float, invert: bool = False) -> np.ndarray:
    """
    Creates bas-relief depth from photos using multi-scale frequency decomposition.
    Smooths flat regions while preserving edges and contours.
    """
    lum = _get_perceptual_luminance(rgb)
    if invert:
        lum = 1.0 - lum

    # Multi-scale decomposition
    # Large scale: global lighting and contours
    large_scale = gaussian_filter(lum, sigma=max(3.0, smoothness * 8.0))
    # Medium scale: facial shapes and object forms
    med_scale = gaussian_filter(lum, sigma=max(1.5, smoothness * 3.0))
    # Detail: textures, wrinkles, embroidery
    detail = lum - med_scale

    # Blend to create cohesive bas-relief
    depth = 0.5 * large_scale + 0.35 * med_scale + 0.15 * (detail + 0.5)

    # Final gentle Gaussian pass for 3D printing smoothness
    depth = gaussian_filter(depth, sigma=max(0.6, smoothness * 1.2))

    # Normalize to [0, 1]
    denom = depth.max() - depth.min()
    if denom > 1e-6:
        depth = (depth - depth.min()) / denom
    else:
        depth = np.zeros_like(depth)

    return depth


def _compute_sketch_lineart_depth(rgb: np.ndarray, smoothness: float, invert: bool = False) -> np.ndarray:
    """
    Converts pencil, charcoal, and ink drawings into embossed or engraved 3D relief.
    """
    lum = _get_perceptual_luminance(rgb)
    
    # Most sketches are dark pencil on light paper
    # Lines should become raised 3D ridges
    base_val = 1.0 - lum if not invert else lum
    
    # Remove paper texture by soft thresholding
    paper_level = np.percentile(base_val, 25)
    adjusted = np.clip((base_val - paper_level) / (1.0 - paper_level + 1e-6), 0.0, 1.0)
    
    # Smooth strokes for clean 3D printing
    sigma = max(0.8, smoothness * 2.0)
    smooth_ridges = gaussian_filter(adjusted, sigma=sigma)
    
    # Non-linear curve to accentuate stroke depth
    depth = np.power(smooth_ridges, 0.8)
    
    denom = depth.max() - depth.min()
    if denom > 1e-6:
        depth = (depth - depth.min()) / denom
    else:
        depth = np.zeros_like(depth)
        
    return depth


def _compute_lithophane_depth(rgb: np.ndarray, smoothness: float) -> np.ndarray:
    """
    Generates depth for 3D printed lithophanes.
    Dark areas are thicker (more opaque), bright areas are thinner (let more light through).
    """
    lum = _get_perceptual_luminance(rgb)
    # Darker pixels -> higher elevation (thicker plastic)
    inv_lum = 1.0 - lum
    
    # Smooth slightly to prevent nozzle stutter on tiny print features
    sigma = max(0.4, smoothness * 0.8)
    depth = gaussian_filter(inv_lum, sigma=sigma)
    
    return depth


def generate_depth_map(
    rgb: np.ndarray,
    alpha: np.ndarray | None,
    mode: ConversionMode | str,
    smoothness: float = 1.0,
    invert: bool = False
) -> np.ndarray:
    """
    Main entry point for depth map generation.
    Returns normalized float32 depth map in range [0.0, 1.0].
    """
    if isinstance(mode, str):
        try:
            mode = ConversionMode(mode.lower())
        except ValueError:
            mode = ConversionMode.PHOTO_RELIEF

    # Clamp smoothness
    smoothness = max(0.1, min(smoothness, 5.0))

    if mode == ConversionMode.ANIME_CARTOON:
        depth = _compute_anime_cartoon_depth(rgb, alpha, smoothness)
    elif mode == ConversionMode.BLUEPRINT:
        depth = _compute_blueprint_depth(rgb, smoothness)
    elif mode == ConversionMode.SKETCH_LINEART:
        depth = _compute_sketch_lineart_depth(rgb, smoothness, invert=invert)
    elif mode == ConversionMode.LITHOPHANE:
        depth = _compute_lithophane_depth(rgb, smoothness)
    else:  # PHOTO_RELIEF
        depth = _compute_photo_relief_depth(rgb, smoothness, invert=invert)

    if invert and mode not in (ConversionMode.SKETCH_LINEART, ConversionMode.PHOTO_RELIEF):
        depth = 1.0 - depth

    return depth.astype(np.float32)
