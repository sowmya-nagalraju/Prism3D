"""
Sample Image Generator for Prism3D
Generates high-quality sample images for each conversion mode:
1. Anime / Cartoon Character (vibrant colorful character illustration)
2. Architectural Blueprint (cyan/blue background with technical floor plan lines)
3. Pencil Sketch (artistic hand-drawn graphite sketch on paper)
4. Photo / Bas-Relief (scenic flower & landscape with depth gradients)
"""

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def generate_all_samples(output_dir: str = "static/samples"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Anime / Cartoon Character (512x512)
    # Vibrant anime chibi character with colorful hair, expressive eyes, and soft clothes
    img_anime = Image.new("RGBA", (512, 512), (248, 246, 252, 255))
    draw = ImageDraw.Draw(img_anime)

    # Character body (cyan/indigo hoodie)
    draw.polygon([(180, 512), (180, 360), (332, 360), (332, 512)], fill=(76, 110, 245, 255))
    draw.polygon([(140, 512), (180, 370), (220, 512)], fill=(66, 99, 235, 255))
    draw.polygon([(372, 512), (332, 370), (292, 512)], fill=(66, 99, 235, 255))
    # Hoodie zipper and trim
    draw.line([(256, 360), (256, 512)], fill=(255, 212, 59, 255), width=6)

    # Neck
    draw.rectangle([(236, 330), (276, 370)], fill=(255, 224, 195, 255))

    # Face base
    draw.ellipse([(176, 170), (336, 350)], fill=(255, 229, 204, 255))
    # Soft blush
    draw.ellipse([(190, 280), (230, 305)], fill=(255, 170, 180, 160))
    draw.ellipse([(282, 280), (322, 305)], fill=(255, 170, 180, 160))

    # Anime eyes
    # Left eye
    draw.ellipse([(205, 240), (235, 280)], fill=(20, 20, 35, 255))
    draw.ellipse([(210, 250), (230, 275)], fill=(224, 49, 134, 255)) # Violet-pink iris
    draw.ellipse([(213, 245), (223, 255)], fill=(255, 255, 255, 255)) # highlight
    draw.ellipse([(225, 265), (230, 270)], fill=(255, 255, 255, 255)) # highlight 2

    # Right eye
    draw.ellipse([(277, 240), (307, 280)], fill=(20, 20, 35, 255))
    draw.ellipse([(282, 250), (302, 275)], fill=(224, 49, 134, 255))
    draw.ellipse([(285, 245), (295, 255)], fill=(255, 255, 255, 255))
    draw.ellipse([(297, 265), (302, 270)], fill=(255, 255, 255, 255))

    # Eyelashes / Eyebrows
    draw.arc([(200, 230), (240, 250)], 190, 350, fill=(33, 37, 41, 255), width=5)
    draw.arc([(272, 230), (312, 250)], 190, 350, fill=(33, 37, 41, 255), width=5)
    # Smile & nose
    draw.arc([(244, 290), (268, 310)], 30, 150, fill=(217, 72, 98, 255), width=4)
    draw.point([(256, 275)], fill=(200, 150, 130, 255))

    # Vibrant anime hair (Coral / Peach / Pink locks)
    hair_color = (255, 107, 107, 255)
    hair_shadow = (238, 82, 83, 255)
    hair_highlight = (255, 168, 168, 255)
    
    # Back hair volume
    draw.ellipse([(140, 130), (372, 380)], fill=hair_shadow)
    # Main hair bangs
    bangs = [
        [(150, 210), (190, 130), (210, 230)],
        [(195, 230), (240, 120), (255, 235)],
        [(250, 235), (275, 120), (315, 225)],
        [(305, 225), (325, 130), (362, 210)],
        [(150, 210), (256, 100), (362, 210), (330, 130), (180, 130)],
    ]
    for b in bangs:
        draw.polygon(b, fill=hair_color)
    
    # Hair shine arc
    draw.arc([(180, 140), (332, 200)], 200, 340, fill=hair_highlight, width=8)

    # Cute cat ears / accessory
    draw.polygon([(160, 140), (180, 60), (220, 120)], fill=(255, 107, 107, 255))
    draw.polygon([(175, 125), (185, 80), (205, 115)], fill=(255, 192, 203, 255))
    draw.polygon([(352, 140), (332, 60), (292, 120)], fill=(255, 107, 107, 255))
    draw.polygon([(337, 125), (327, 80), (307, 115)], fill=(255, 192, 203, 255))

    img_anime.convert("RGB").save(out_path / "anime_character.png")

    # 2. Architectural Blueprint (512x512)
    # Deep cyan blueprint background with crisp white CAD floor plan lines
    img_blue = Image.new("RGB", (512, 512), (14, 52, 105))
    draw_blue = ImageDraw.Draw(img_blue)

    # Grid background lines (technical graph paper feel)
    for i in range(0, 512, 32):
        draw_blue.line([(0, i), (512, i)], fill=(20, 65, 125), width=1)
        draw_blue.line([(i, 0), (i, 512)], fill=(20, 65, 125), width=1)

    # Outer building walls (thick white CAD lines)
    wall_col = (255, 255, 255)
    inner_wall_col = (220, 235, 255)
    thick = 6

    # Perimeter walls
    draw_blue.line([(64, 64), (448, 64)], fill=wall_col, width=thick)
    draw_blue.line([(448, 64), (448, 448)], fill=wall_col, width=thick)
    draw_blue.line([(448, 448), (64, 448)], fill=wall_col, width=thick)
    draw_blue.line([(64, 448), (64, 64)], fill=wall_col, width=thick)

    # Interior room dividers
    draw_blue.line([(256, 64), (256, 320)], fill=wall_col, width=thick)
    draw_blue.line([(64, 256), (256, 256)], fill=wall_col, width=thick)
    draw_blue.line([(256, 320), (448, 320)], fill=wall_col, width=thick)
    draw_blue.line([(352, 320), (352, 448)], fill=wall_col, width=thick)

    # Door swing arcs & openings
    draw_blue.arc([(180, 200), (256, 276)], 0, 90, fill=(160, 210, 255), width=2)
    draw_blue.line([(218, 256), (256, 256)], fill=(14, 52, 105), width=thick + 2) # door opening

    draw_blue.arc([(256, 140), (332, 216)], 270, 360, fill=(160, 210, 255), width=2)
    draw_blue.line([(256, 178), (256, 216)], fill=(14, 52, 105), width=thick + 2)

    # Technical CAD circle & columns
    draw_blue.ellipse([(140, 140), (180, 180)], outline=inner_wall_col, width=3)
    draw_blue.ellipse([(330, 140), (370, 180)], outline=inner_wall_col, width=3)
    draw_blue.rectangle([(145, 335), (175, 365)], fill=inner_wall_col)
    draw_blue.rectangle([(390, 370), (410, 390)], fill=inner_wall_col)

    # Architectural dimension arrows & labels
    draw_blue.line([(48, 64), (48, 448)], fill=(100, 180, 240), width=2)
    draw_blue.line([(42, 64), (54, 64)], fill=(100, 180, 240), width=2)
    draw_blue.line([(42, 448), (54, 448)], fill=(100, 180, 240), width=2)
    draw_blue.line([(64, 464), (448, 464)], fill=(100, 180, 240), width=2)
    draw_blue.line([(64, 458), (64, 470)], fill=(100, 180, 240), width=2)
    draw_blue.line([(448, 458), (448, 470)], fill=(100, 180, 240), width=2)

    img_blue.save(out_path / "architectural_blueprint.png")

    # 3. Artistic Pencil Sketch (512x512)
    # Warm cream paper with graphite strokes of a majestic lion/animal emblem
    img_sketch = Image.new("RGB", (512, 512), (245, 241, 232))
    draw_sketch = ImageDraw.Draw(img_sketch)

    # Shading and concentric hand-drawn curves
    center_x, center_y = 256, 256
    for r in range(40, 200, 8):
        # Organic wavy circles (rose/mandala/lion mane)
        points = []
        petals = 12
        for angle_deg in range(0, 365, 5):
            rad = math.radians(angle_deg)
            warp = 10 * math.sin(petals * rad) + 5 * math.cos(3 * rad)
            px = center_x + (r + warp) * math.cos(rad)
            py = center_y + (r + warp) * math.sin(rad)
            points.append((px, py))
        
        # Graphite gray shades
        gray = int(50 + (200 - r) * 0.4)
        draw_sketch.line(points, fill=(gray, gray, gray), width=3)

    # Central artistic motif
    draw_sketch.ellipse([(206, 206), (306, 306)], outline=(30, 30, 30), width=5)
    draw_sketch.polygon([(256, 216), (296, 286), (216, 286)], fill=(50, 50, 50))
    draw_sketch.polygon([(256, 296), (296, 226), (216, 226)], fill=(90, 90, 90))

    # Cross-hatching pencil texture
    for offset in range(-150, 150, 15):
        draw_sketch.line([(256 + offset, 130), (256 + offset + 40, 380)], fill=(180, 175, 165), width=1)

    img_sketch.save(out_path / "pencil_sketch.png")

    # 4. Vibrant Photo / Bas-Relief (512x512)
    # Beautiful radial gradient flower/starburst with vivid petals and deep shadows
    arr = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    cx, cy = 256, 256
    dist_from_c = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    angle = np.arctan2(y - cy, x - cx)

    # Multi-frequency petal geometry
    num_petals = 8
    petal_wave = np.sin(num_petals * angle) * 45
    radius_profile = np.clip(1.0 - (dist_from_c - petal_wave) / 220.0, 0.0, 1.0)

    # Vibrant emerald, teal, and gold colors
    r_chan = (np.sin(dist_from_c * 0.05) * 80 + 175 * radius_profile).astype(np.uint8)
    g_chan = (np.cos(angle * 4) * 50 + 200 * radius_profile).astype(np.uint8)
    b_chan = (np.sin(angle * 2) * 90 + 230 * radius_profile).astype(np.uint8)

    arr[:, :, 0] = np.clip(r_chan, 20, 255)
    arr[:, :, 1] = np.clip(g_chan, 30, 255)
    arr[:, :, 2] = np.clip(b_chan, 40, 255)

    img_photo = Image.fromarray(arr)
    # Smooth bloom
    img_photo = img_photo.filter(ImageFilter.SMOOTH_MORE)
    img_photo.save(out_path / "vibrant_photo.png")

    print(f"Generated 4 sample images in {out_path.resolve()}")


if __name__ == "__main__":
    generate_all_samples()
