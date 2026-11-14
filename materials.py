from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import numpy as np
import trimesh


@dataclass(frozen=True)
class MaterialPreset:
    name: str
    category: str  # wood, stone, metal, building, organic, glass, synthetic, terrain
    base_color_rgba: Tuple[int, int, int, int]
    roughness: float  # 0.0 (bóng gương) -> 1.0 (lì hoàn toàn)
    metallic: float   # 0.0 (phi kim) -> 1.0 (kim loại)
    tags: Tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


MATERIALS: Dict[str, MaterialPreset] = {
    # --- Gỗ ---
    "wood_oak": MaterialPreset("wood_oak", "wood", (155, 108, 66, 255), 0.72, 0.0, ("go", "soi", "ban", "cua")),
    "wood_pine": MaterialPreset("wood_pine", "wood", (196, 156, 108, 255), 0.68, 0.0, ("go", "thong", "nhat")),
    "wood_dark": MaterialPreset("wood_dark", "wood", (82, 52, 34, 255), 0.65, 0.0, ("go", "toi", "tram")),
    "wood_plank": MaterialPreset("wood_plank", "wood", (142, 98, 58, 255), 0.78, 0.0, ("van", "san", "hang_rao")),

    # --- Đá & Địa hình ---
    "stone_rough": MaterialPreset("stone_rough", "stone", (128, 126, 120, 255), 0.88, 0.0, ("da", "tho", "nui", "tang_da")),
    "stone_cut": MaterialPreset("stone_cut", "stone", (158, 155, 148, 255), 0.62, 0.0, ("da", "mai", "tru", "bac_thang")),
    "stone_slate": MaterialPreset("stone_slate", "stone", (78, 84, 92, 255), 0.58, 0.0, ("da", "den", "mai_ngoi")),
    "terrain_grass": MaterialPreset("terrain_grass", "terrain", (84, 148, 62, 255), 0.90, 0.0, ("co", "san", "dat")),
    "terrain_dirt": MaterialPreset("terrain_dirt", "terrain", (126, 92, 62, 255), 0.94, 0.0, ("dat", "bun", "duong")),
    "terrain_sand": MaterialPreset("terrain_sand", "terrain", (214, 192, 140, 255), 0.86, 0.0, ("cat", "sa_mac")),

    # --- Xây dựng / Nhà cửa ---
    "brick_red": MaterialPreset("brick_red", "building", (168, 68, 54, 255), 0.82, 0.0, ("gach", "tuong", "nha")),
    "brick_old": MaterialPreset("brick_old", "building", (132, 64, 56, 255), 0.88, 0.0, ("gach", "cu", "co")),
    "concrete_plain": MaterialPreset("concrete_plain", "building", (168, 168, 164, 255), 0.85, 0.0, ("be_tong", "tuong", "cot")),
    "plaster_white": MaterialPreset("plaster_white", "building", (232, 228, 220, 255), 0.75, 0.0, ("voi", "tuong", "tran")),
    "roof_tile_red": MaterialPreset("roof_tile_red", "building", (152, 58, 42, 255), 0.66, 0.0, ("ngoi", "mai", "nha")),
    "roof_tile_blue": MaterialPreset("roof_tile_blue", "building", (58, 76, 104, 255), 0.62, 0.0, ("ngoi", "mai", "xanh")),

    # --- Kim loại ---
    "metal_steel": MaterialPreset("metal_steel", "metal", (185, 190, 196, 255), 0.34, 0.90, ("thep", "sat", "khung")),
    "metal_iron_rust": MaterialPreset("metal_iron_rust", "metal", (134, 76, 48, 255), 0.80, 0.65, ("gi", "sat", "cu")),
    "metal_gold": MaterialPreset("metal_gold", "metal", (232, 188, 72, 255), 0.24, 0.95, ("vang", "dong_thau")),
    "metal_copper": MaterialPreset("metal_copper", "metal", (198, 112, 74, 255), 0.30, 0.92, ("dong", "ong")),
    "metal_dark": MaterialPreset("metal_dark", "metal", (54, 58, 64, 255), 0.42, 0.85, ("den", "may", "phu_kien")),

    # --- Nhân vật / Hữu cơ / Vải ---
    "skin_base": MaterialPreset("skin_base", "organic", (222, 178, 152, 255), 0.60, 0.0, ("da", "nhan_vat", "nguoi")),
    "cloth_canvas": MaterialPreset("cloth_canvas", "organic", (176, 162, 136, 255), 0.88, 0.0, ("vai", "ao", "bo_bo")),
    "cloth_dark": MaterialPreset("cloth_dark", "organic", (46, 50, 58, 255), 0.85, 0.0, ("vai", "den", "quan")),
    "leather_brown": MaterialPreset("leather_brown", "organic", (112, 68, 42, 255), 0.52, 0.0, ("da_thuoc", "day", "giap")),

    # --- Kính / Nhựa / Tiện ích ---
    "glass_clear": MaterialPreset("glass_clear", "glass", (205, 232, 245, 110), 0.08, 0.0, ("kinh", "cua_so", "trong")),
    "plastic_matte": MaterialPreset("plastic_matte", "synthetic", (190, 190, 195, 255), 0.48, 0.0, ("nhua", "blockout")),
    "plastic_gloss": MaterialPreset("plastic_gloss", "synthetic", (210, 210, 218, 255), 0.16, 0.0, ("nhua", "bong")),
}

ALIAS_MAP: Dict[str, str] = {
    "go": "wood_oak",
    "wood": "wood_oak",
    "da": "stone_rough",
    "stone": "stone_rough",
    "gach": "brick_red",
    "brick": "brick_red",
    "be_tong": "concrete_plain",
    "concrete": "concrete_plain",
    "ngoi": "roof_tile_red",
    "roof": "roof_tile_red",
    "thep": "metal_steel",
    "steel": "metal_steel",
    "vang": "metal_gold",
    "gold": "metal_gold",
    "kinh": "glass_clear",
    "glass": "glass_clear",
    "co": "terrain_grass",
    "grass": "terrain_grass",
    "dat": "terrain_dirt",
    "dirt": "terrain_dirt",
    "vai": "cloth_canvas",
    "cloth": "cloth_canvas",
    "skin": "skin_base",
}


def get_material(name: str, fallback: str = "plastic_matte") -> MaterialPreset:
    key = name.strip().lower()
    if key in MATERIALS:
        return MATERIALS[key]
    if key in ALIAS_MAP and ALIAS_MAP[key] in MATERIALS:
        return MATERIALS[ALIAS_MAP[key]]
    for preset in MATERIALS.values():
        if key in preset.tags or key in preset.name:
            return preset
    return MATERIALS[fallback]


def list_materials(category: Optional[str] = None) -> List[dict]:
    items = MATERIALS.values()
    if category:
        items = [m for m in items if m.category == category.lower()]
    return [m.to_dict() for m in items]


def apply_material(mesh: trimesh.Trimesh, material_name: str) -> trimesh.Trimesh:
    preset = get_material(material_name)
    rgba = preset.base_color_rgba
    mat = trimesh.visual.material.PBRMaterial(
        baseColorFactor=rgba,
        roughnessFactor=preset.roughness,
        metallicFactor=preset.metallic,
    )
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, material=mat)
    mesh.visual.face_colors = np.tile(np.array(rgba, dtype=np.uint8), (len(mesh.faces), 1))
    return mesh
    