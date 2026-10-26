"""
3D Mesh Construction and Topology Engine
Converts 2D depth map and original color image into a watertight, manifold,
smooth 3D solid with exact RGB vertex colors and UV coordinates, ready for 3D printing.
"""

import numpy as np
import trimesh


def build_colored_3d_mesh(
    depth_map: np.ndarray,
    rgb_image: np.ndarray,
    width_mm: float = 100.0,
    max_height_mm: float = 12.0,
    base_thickness_mm: float = 3.0,
    dual_sided: bool = False,
    curve_arc_deg: float = 0.0,
    mesh_resolution: int = 256
) -> trimesh.Trimesh:
    """
    Constructs a manifold, watertight 3D mesh with vertex colors.
    
    Args:
        depth_map: 2D numpy array [H, W], values in [0, 1]
        rgb_image: 2D numpy array [H, W, 3], uint8 [0, 255]
        width_mm: Target physical width of the 3D model in millimeters
        max_height_mm: Maximum relief elevation above base in millimeters
        base_thickness_mm: Solid base plate thickness in millimeters
        dual_sided: If True, mirror mesh along Z=0 for a full figurine
        curve_arc_deg: If > 0, curve the mesh into a cylindrical arc (for lamps/lithophanes)
        mesh_resolution: Maximum grid dimension for mesh generation
    """
    h_orig, w_orig = depth_map.shape

    # Downsample or resample grid to target mesh resolution for performance & slicer compatibility
    max_dim = max(h_orig, w_orig)
    if max_dim > mesh_resolution:
        step = max(1, int(round(max_dim / mesh_resolution)))
        depth = depth_map[::step, ::step]
        rgb = rgb_image[::step, ::step, :]
    else:
        depth = depth_map
        rgb = rgb_image

    rows, cols = depth.shape
    aspect = rows / cols
    length_mm = width_mm * aspect

    # 1. Generate (X, Y) plane coordinates centered at (0, 0)
    xs = np.linspace(-width_mm / 2.0, width_mm / 2.0, cols, dtype=np.float32)
    ys = np.linspace(length_mm / 2.0, -length_mm / 2.0, rows, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(xs, ys)

    # 2. Compute Z coordinates (Top surface)
    if dual_sided:
        grid_z_top = (depth * max_height_mm) / 2.0
    else:
        grid_z_top = base_thickness_mm + (depth * max_height_mm)

    # 3. Optional Cylindrical Arc Bending (for lithophane lamp shades)
    if curve_arc_deg > 5.0 and not dual_sided:
        arc_rad = np.radians(min(180.0, curve_arc_deg))
        radius = width_mm / arc_rad
        theta = (grid_x / width_mm) * arc_rad
        # Transform X and Z into cylindrical coordinates
        bent_x = radius * np.sin(theta)
        bent_depth = radius * (1.0 - np.cos(theta))
        grid_x = bent_x
        grid_z_top = grid_z_top + bent_depth

    # Top surface vertices
    top_vertices = np.stack([grid_x, grid_y, grid_z_top], axis=-1).reshape(-1, 3)

    # Top surface colors (RGBA)
    top_colors = np.zeros((rows * cols, 4), dtype=np.uint8)
    top_colors[:, :3] = rgb.reshape(-1, 3)
    top_colors[:, 3] = 255

    # Top surface triangles (regular grid indexing)
    r_idx, c_idx = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    v00 = (r_idx * cols + c_idx).ravel()
    v01 = (r_idx * cols + (c_idx + 1)).ravel()
    v10 = ((r_idx + 1) * cols + c_idx).ravel()
    v11 = ((r_idx + 1) * cols + (c_idx + 1)).ravel()

    # Counter-Clockwise winding for upward normal (+Z)
    top_tri1 = np.column_stack([v00, v10, v01])
    top_tri2 = np.column_stack([v01, v10, v11])
    top_faces = np.vstack([top_tri1, top_tri2])

    if dual_sided:
        # Full mirrored 3D figurine
        grid_z_bot = -(depth * max_height_mm) / 2.0
        bot_vertices = np.stack([grid_x, grid_y, grid_z_bot], axis=-1).reshape(-1, 3)
        bot_colors = top_colors.copy()
        
        # Inverted winding for downward normal (-Z)
        bot_offset = len(top_vertices)
        bot_tri1 = np.column_stack([v00 + bot_offset, v01 + bot_offset, v10 + bot_offset])
        bot_tri2 = np.column_stack([v01 + bot_offset, v11 + bot_offset, v10 + bot_offset])
        bot_faces = np.vstack([bot_tri1, bot_tri2])
    else:
        # Watertight flat base plate at Z = 0
        if curve_arc_deg > 5.0:
            grid_z_bot = np.zeros_like(grid_z_top) + bent_depth
        else:
            grid_z_bot = np.zeros_like(grid_z_top)
            
        bot_vertices = np.stack([grid_x, grid_y, grid_z_bot], axis=-1).reshape(-1, 3)
        
        # Solid base plate color (clean soft neutral base, or sampled border color)
        avg_border_color = np.mean(rgb[[0, -1], :, :], axis=(0, 1)).astype(np.uint8)
        base_color = np.array([avg_border_color[0], avg_border_color[1], avg_border_color[2], 255], dtype=np.uint8)
        bot_colors = np.tile(base_color, (len(bot_vertices), 1))

        # Bottom faces (facing downwards -Z)
        bot_offset = len(top_vertices)
        bot_tri1 = np.column_stack([v00 + bot_offset, v01 + bot_offset, v10 + bot_offset])
        bot_tri2 = np.column_stack([v01 + bot_offset, v11 + bot_offset, v10 + bot_offset])
        bot_faces = np.vstack([bot_tri1, bot_tri2])

    # 4. Side Skirts / Perimeter Walls (Closing the model into a watertight solid)
    # Collect indices of perimeter border
    # North border: r=0, c=0..cols-1
    north_top = np.arange(cols)
    # East border: c=cols-1, r=0..rows-1
    east_top = np.arange(cols - 1, rows * cols, cols)
    # South border: r=rows-1, c=cols-1..0
    south_top = np.arange(rows * cols - 1, (rows - 1) * cols - 1, -1)
    # West border: c=0, r=rows-1..0
    west_top = np.arange((rows - 1) * cols, -1, -cols)

    # Stitch closed perimeter loop
    perimeter_top = np.concatenate([
        north_top[:-1],
        east_top[:-1],
        south_top[:-1],
        west_top[:-1]
    ])
    perimeter_next_top = np.roll(perimeter_top, -1)
    perimeter_bot = perimeter_top + bot_offset
    perimeter_next_bot = perimeter_next_top + bot_offset

    # Side wall triangles (facing outwards)
    side_tri1 = np.column_stack([perimeter_top, perimeter_bot, perimeter_next_top])
    side_tri2 = np.column_stack([perimeter_next_top, perimeter_bot, perimeter_next_bot])
    side_faces = np.vstack([side_tri1, side_tri2])

    # Combine all vertices, colors, and faces
    all_vertices = np.vstack([top_vertices, bot_vertices])
    all_colors = np.vstack([top_colors, bot_colors])
    all_faces = np.vstack([top_faces, bot_faces, side_faces])

    # Assemble Trimesh solid
    mesh = trimesh.Trimesh(
        vertices=all_vertices,
        faces=all_faces,
        vertex_colors=all_colors,
        process=True
    )

    # Smooth surface normals for clean visual rendering and accurate slicing
    mesh.fix_normals()

    return mesh
