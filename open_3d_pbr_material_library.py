from __future__ import annotations

import csv
import hashlib
import itertools
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class PBRChannels:
    """Thông số kênh PBR chuẩn (tương thích glTF 2.0 / Blender Principled BSDF / MaterialX)."""

    base_color_hex: str
    base_color_rgb: Tuple[float, float, float]  # [0.0, 1.0] linear/sRGB reference
    metallic: float                             # [0.0, 1.0]
    roughness: float                            # [0.0, 1.0]
    ior: float = 1.45                           # Index of Refraction
    specular: float = 0.5                       # [0.0, 1.0]
    clearcoat: float = 0.0                      # [0.0, 1.0]
    clearcoat_roughness: float = 0.03           # [0.0, 1.0]
    transmission: float = 0.0                   # [0.0, 1.0] (kính, nước, pha lê)
    subsurface: float = 0.0                     # [0.0, 1.0] (da, sáp, đá cẩm thạch mỏng)
    subsurface_radius: Tuple[float, float, float] = (0.8, 0.35, 0.18)  # Tán xạ dưới bề mặt RGB
    sheen: float = 0.0                          # [0.0, 1.0] (vải nhung, nỉ)
    normal_strength: float = 1.0                # Cường độ Normal map
    height_scale: float = 0.02                  # Độ sâu Displacement/Parallax (mét)


@dataclass
class PBRMaterial3D:
    """Bản ghi chuẩn cho một vật liệu 3D trong kho mã nguồn mở phục vụ AI 3D."""

    material_id: str
    name: str
    category: str
    subcategory: str
    license: str
    pbr: PBRChannels
    required_maps: List[str]
    surface_traits: List[str]
    ai_caption: str
    ai_tags: List[str]
    metadata: Dict[str, str] = field(default_factory=dict)


# ==============================================================================
# 1. BỘ PRESET CỐT LÕI CHO KHO VẬT LIỆU 3D (DỄ MỞ RỘNG)
# ==============================================================================
BASE_3D_PRESETS: List[dict] = [
    # --- KIM LOẠI 3D ---
    {
        "name": "Brushed Anodized Aluminum",
        "category": "Metal",
        "subcategory": "Anodized",
        "base_color_hex": "#7D8B99",
        "metallic": 0.96,
        "roughness": 0.28,
        "ior": 1.44,
        "clearcoat": 0.15,
        "normal_strength": 0.45,
        "height_scale": 0.003,
        "required_maps": ["basecolor", "normal", "roughness", "metallic", "ao"],
        "surface_traits": ["directional_grain", "micro_scratches", "anisotropic_sheen"],
        "ai_tags": ["metal", "aluminum", "brushed", "anodized", "industrial", "hard_surface"],
    },
    {
        "name": "Rusted Corrugated Iron",
        "category": "Metal",
        "subcategory": "Weathered",
        "base_color_hex": "#6E3B24",
        "metallic": 0.42,
        "roughness": 0.84,
        "ior": 1.52,
        "normal_strength": 1.35,
        "height_scale": 0.025,
        "required_maps": ["basecolor", "normal", "roughness", "metallic", "height", "ao"],
        "surface_traits": ["flaky_oxide", "pitted_surface", "color_variation"],
        "ai_tags": ["metal", "rust", "iron", "weathered", "abandoned", "grunge"],
    },
    {
        "name": "Hammered Copper Patina",
        "category": "Metal",
        "subcategory": "Patina",
        "base_color_hex": "#4F7D6E",
        "metallic": 0.55,
        "roughness": 0.62,
        "ior": 1.48,
        "normal_strength": 1.15,
        "height_scale": 0.015,
        "required_maps": ["basecolor", "normal", "roughness", "metallic", "ao"],
        "surface_traits": ["hammer_dimples", "verdigris_oxidation", "warm_highlight"],
        "ai_tags": ["metal", "copper", "patina", "hammered", "oxidized", "artisan"],
    },
    {
        "name": "Damascus Folded Steel",
        "category": "Metal",
        "subcategory": "Patterned",
        "base_color_hex": "#4A4E54",
        "metallic": 0.94,
        "roughness": 0.34,
        "ior": 1.50,
        "normal_strength": 0.70,
        "height_scale": 0.005,
        "required_maps": ["basecolor", "normal", "roughness", "metallic", "height"],
        "surface_traits": ["wave_layers", "etched_contrast", "fine_polish"],
        "ai_tags": ["metal", "steel", "damascus", "blade", "weapon", "layered"],
    },
    # --- GỖ 3D ---
    {
        "name": "Reclaimed Barn Oak Plank",
        "category": "Wood",
        "subcategory": "Plank",
        "base_color_hex": "#5C432D",
        "metallic": 0.0,
        "roughness": 0.76,
        "ior": 1.53,
        "normal_strength": 1.20,
        "height_scale": 0.018,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["wood_fiber", "nail_holes", "split_grain"],
        "ai_tags": ["wood", "oak", "reclaimed", "plank", "architecture", "rustic"],
    },
    {
        "name": "Lacquer Walnut Veneer",
        "category": "Wood",
        "subcategory": "Polished",
        "base_color_hex": "#3B2314",
        "metallic": 0.0,
        "roughness": 0.18,
        "ior": 1.54,
        "clearcoat": 0.85,
        "clearcoat_roughness": 0.06,
        "normal_strength": 0.30,
        "height_scale": 0.002,
        "required_maps": ["basecolor", "normal", "roughness", "ao"],
        "surface_traits": ["tight_grain", "gloss_varnish", "deep_tone"],
        "ai_tags": ["wood", "walnut", "lacquered", "furniture", "interior", "glossy"],
    },
    # --- ĐÁ & ĐỊA CHẤT 3D ---
    {
        "name": "Veined Carrara Marble",
        "category": "Stone",
        "subcategory": "Marble",
        "base_color_hex": "#E6E4DF",
        "metallic": 0.0,
        "roughness": 0.22,
        "ior": 1.49,
        "subsurface": 0.12,
        "clearcoat": 0.35,
        "normal_strength": 0.25,
        "height_scale": 0.002,
        "required_maps": ["basecolor", "normal", "roughness", "ao"],
        "surface_traits": ["grey_veins", "crystalline_luster", "soft_diffusion"],
        "ai_tags": ["stone", "marble", "carrara", "veined", "luxury", "interior"],
    },
    {
        "name": "Porous Volcanic Basalt",
        "category": "Stone",
        "subcategory": "Volcanic",
        "base_color_hex": "#2F3134",
        "metallic": 0.0,
        "roughness": 0.88,
        "ior": 1.58,
        "normal_strength": 1.45,
        "height_scale": 0.030,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["vesicular_pores", "sharp_edges", "matte_mineral"],
        "ai_tags": ["stone", "basalt", "volcanic", "rock", "terrain", "rough"],
    },
    # --- VẢI & DỆT 3D ---
    {
        "name": "Heavy Woven Linen",
        "category": "Fabric",
        "subcategory": "Woven",
        "base_color_hex": "#C8B89E",
        "metallic": 0.0,
        "roughness": 0.86,
        "ior": 1.47,
        "sheen": 0.65,
        "normal_strength": 0.95,
        "height_scale": 0.008,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["warp_weft_weave", "slub_threads", "soft_fuzz"],
        "ai_tags": ["fabric", "linen", "woven", "textile", "soft_body", "clothing"],
    },
    {
        "name": "Ripstop Tactical Nylon",
        "category": "Fabric",
        "subcategory": "Synthetic",
        "base_color_hex": "#3A4436",
        "metallic": 0.0,
        "roughness": 0.54,
        "ior": 1.53,
        "sheen": 0.25,
        "normal_strength": 0.80,
        "height_scale": 0.006,
        "required_maps": ["basecolor", "normal", "roughness", "height"],
        "surface_traits": ["grid_ripstop", "water_repellent_sheen", "tight_knit"],
        "ai_tags": ["fabric", "nylon", "ripstop", "tactical", "gear", "backpack"],
    },
    # --- DA & SINH HỌC 3D ---
    {
        "name": "Distressed Saddle Leather",
        "category": "Organic",
        "subcategory": "Leather",
        "base_color_hex": "#6B3E23",
        "metallic": 0.0,
        "roughness": 0.58,
        "ior": 1.50,
        "subsurface": 0.05,
        "normal_strength": 0.90,
        "height_scale": 0.010,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["follicle_pores", "creases", "worn_patina"],
        "ai_tags": ["leather", "saddle", "distressed", "organic", "prop", "wearable"],
    },
    {
        "name": "Rich Ebony Dark Skin",
        "category": "Organic",
        "subcategory": "HumanSkin_Dark",
        "base_color_hex": "#2B1710",
        "metallic": 0.0,
        "roughness": 0.46,
        "ior": 1.43,
        "specular": 0.58,
        "clearcoat": 0.14,
        "clearcoat_roughness": 0.24,
        "subsurface": 0.42,
        "subsurface_radius": (0.72, 0.26, 0.14),
        "normal_strength": 0.78,
        "height_scale": 0.005,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao", "subsurface"],
        "surface_traits": [
            "micro_pore_network",
            "fine_wrinkle_lines",
            "epidermal_ridge_pattern",
            "warm_reddish_undertone",
            "sebaceous_sheen_zones",
            "knuckle_flex_creases",
            "subtle_vellus_peach_fuzz",
            "follicular_texture",
            "soft_sss_rim_glow",
            "moisture_micro_variation",
        ],
        "ai_tags": [
            "skin",
            "dark_skin",
            "ebony_skin",
            "melanin_rich",
            "human_anatomy",
            "organic",
            "subsurface_scattering",
            "character_3d",
            "portrait_pbr",
            "pore_detail",
        ],
    },
    {
        "name": "Deep Espresso Oily Dark Skin",
        "category": "Organic",
        "subcategory": "HumanSkin_Dark",
        "base_color_hex": "#1F100B",
        "metallic": 0.0,
        "roughness": 0.29,
        "ior": 1.44,
        "specular": 0.65,
        "clearcoat": 0.36,
        "clearcoat_roughness": 0.14,
        "subsurface": 0.48,
        "subsurface_radius": (0.68, 0.22, 0.12),
        "normal_strength": 0.72,
        "height_scale": 0.004,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao", "subsurface"],
        "surface_traits": [
            "t_zone_sebum_highlight",
            "dilated_pores",
            "specular_sweat_beads",
            "warm_mahogany_subsurface",
            "fine_expression_creases",
            "smooth_cheek_contours",
            "textured_nose_bridge",
            "glossy_lip_margin_transition",
        ],
        "ai_tags": [
            "skin",
            "dark_skin",
            "espresso_skin",
            "oily_skin",
            "sweaty",
            "subsurface_scattering",
            "character_3d",
            "realistic_human",
        ],
    },
    {
        "name": "Ashy Matte Textured Dark Skin",
        "category": "Organic",
        "subcategory": "HumanSkin_Dark",
        "base_color_hex": "#38221A",
        "metallic": 0.0,
        "roughness": 0.74,
        "ior": 1.42,
        "specular": 0.42,
        "clearcoat": 0.0,
        "subsurface": 0.34,
        "subsurface_radius": (0.75, 0.28, 0.15),
        "normal_strength": 1.05,
        "height_scale": 0.008,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao", "subsurface"],
        "surface_traits": [
            "dry_micro_flaking",
            "ashy_desaturated_highlights",
            "deep_pore_relief",
            "calloused_palm_ridges",
            "elbow_knee_folding",
            "chalky_friction_patches",
            "high_frequency_grain",
        ],
        "ai_tags": [
            "skin",
            "dark_skin",
            "dry_skin",
            "ashy_skin",
            "matte_organic",
            "survival_character",
            "high_detail_pores",
        ],
    },
    # --- THỦY TINH & PHA LÊ 3D ---
    {
        "name": "Frosted Architectural Glass",
        "category": "Glass",
        "subcategory": "Frosted",
        "base_color_hex": "#DCE8EC",
        "metallic": 0.0,
        "roughness": 0.42,
        "ior": 1.52,
        "transmission": 0.88,
        "normal_strength": 0.55,
        "height_scale": 0.004,
        "required_maps": ["basecolor", "normal", "roughness", "transmission"],
        "surface_traits": ["micro_etched", "diffused_refraction", "edge_tint"],
        "ai_tags": ["glass", "frosted", "translucent", "architecture", "window", "optical"],
    },
    # --- NHỰA & CAO SU 3D ---
    {
        "name": "Injection Molded ABS",
        "category": "Polymer",
        "subcategory": "Rigid",
        "base_color_hex": "#25282C",
        "metallic": 0.0,
        "roughness": 0.36,
        "ior": 1.54,
        "clearcoat": 0.10,
        "normal_strength": 0.35,
        "height_scale": 0.002,
        "required_maps": ["basecolor", "normal", "roughness", "ao"],
        "surface_traits": ["spark_eroded_texture", "subtle_mold_seam"],
        "ai_tags": ["plastic", "abs", "electronics", "housing", "hard_surface", "consumer"],
    },
    {
        "name": "Treaded Vulcanized Rubber",
        "category": "Polymer",
        "subcategory": "Elastomer",
        "base_color_hex": "#1E1F22",
        "metallic": 0.0,
        "roughness": 0.78,
        "ior": 1.52,
        "normal_strength": 1.25,
        "height_scale": 0.022,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["tread_grooves", "micro_grain", "non_reflective"],
        "ai_tags": ["rubber", "tire", "elastomer", "vehicle", "industrial", "matte"],
    },
    # --- GỐM & SỨ 3D ---
    {
        "name": "Crackle Celadon Ceramic",
        "category": "Ceramic",
        "subcategory": "Glazed",
        "base_color_hex": "#7FA696",
        "metallic": 0.0,
        "roughness": 0.14,
        "ior": 1.55,
        "clearcoat": 0.90,
        "clearcoat_roughness": 0.04,
        "normal_strength": 0.50,
        "height_scale": 0.003,
        "required_maps": ["basecolor", "normal", "roughness", "ao"],
        "surface_traits": ["crazing_network", "gloss_glaze", "pooled_color"],
        "ai_tags": ["ceramic", "celadon", "crackle", "glazed", "pottery", "decor"],
    },
    # --- KIẾN TRÚC & TƯỜNG 3D ---
    {
        "name": "Weathered Red Brick Masonry",
        "category": "Architecture",
        "subcategory": "Masonry",
        "base_color_hex": "#8A3B2B",
        "metallic": 0.0,
        "roughness": 0.85,
        "ior": 1.56,
        "normal_strength": 1.40,
        "height_scale": 0.028,
        "required_maps": ["basecolor", "normal", "roughness", "height", "ao"],
        "surface_traits": ["mortar_joints", "efflorescence", "clay_pitting"],
        "ai_tags": ["brick", "masonry", "wall", "architecture", "building", "exterior"],
    },
    # --- SCI-FI & ĐẶC BIỆT 3D ---
    {
        "name": "Hexagonal Carbon Lattice Composite",
        "category": "SciFi_Composite",
        "subcategory": "Carbon",
        "base_color_hex": "#2B2D33",
        "metallic": 0.25,
        "roughness": 0.31,
        "ior": 1.58,
        "clearcoat": 0.65,
        "clearcoat_roughness": 0.08,
        "normal_strength": 0.85,
        "height_scale": 0.007,
        "required_maps": ["basecolor", "normal", "roughness", "metallic", "height"],
        "surface_traits": ["hex_weave", "resin_gloss", "directional_reflectance"],
        "ai_tags": ["carbon_fiber", "composite", "scifi", "aerospace", "automotive", "tech"],
    },
]


def hex_to_rgb01(hex_color: str) -> Tuple[float, float, float]:
    clean = hex_color.lstrip("#")
    r, g, b = int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)
    return (round(r / 255.0, 4), round(g / 255.0, 4), round(b / 255.0, 4))


def rgb01_to_hex(rgb: Tuple[float, float, float]) -> str:
    r = max(0, min(255, round(rgb[0] * 255)))
    g = max(0, min(255, round(rgb[1] * 255)))
    b = max(0, min(255, round(rgb[2] * 255)))
    return f"#{r:02X}{g:02X}{b:02X}"


def clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return round(max(lo, min(hi, val)), 4)


# ==============================================================================
# 2. BỘ SINH & QUẢN LÝ KHO VẬT LIỆU 3D MÃ NGUỒN MỞ (SCALE LÊN HÀNG NGHÌN)
# ==============================================================================
class Open3DMaterialLibrary:
    """Kho vật liệu 3D mã nguồn mở có khả năng sinh hàng nghìn biến thể PBR chuẩn cho AI."""

    WEAR_STATES = {
        "pristine": ("Pristine", 0.0, -0.06, 0.0, ["clean", "mint"]),
        "lightly_worn": ("Lightly Worn", 0.15, 0.04, 0.05, ["subtle_wear", "daily_use"]),
        "weathered": ("Weathered", 0.35, 0.14, 0.15, ["weathered", "aged", "patina"]),
        "battle_damaged": ("Battle Damaged", 0.55, 0.22, 0.28, ["scratched", "dented", "heavy_wear"]),
        "mossy_damp": ("Mossy & Damp", 0.25, -0.10, 0.12, ["damp", "organic_growth", "outdoor"]),
    }

    FINISH_MODIFIERS = {
        "matte": ("Matte", 0.22, 0.0, ["matte", "diffuse"]),
        "satin": ("Satin", 0.04, 0.15, ["satin", "soft_gloss"]),
        "semi_gloss": ("Semi-Gloss", -0.10, 0.45, ["semi_gloss", "lacquered"]),
        "high_gloss": ("High-Gloss", -0.22, 0.85, ["glossy", "reflective"]),
    }

    COLOR_SHIFTS = {
        "neutral": ("Neutral", (0.0, 0.0, 0.0)),
        "warm": ("Warm", (0.06, 0.02, -0.04)),
        "cool": ("Cool", (-0.04, 0.01, 0.07)),
        "dark": ("Dark", (-0.14, -0.14, -0.14)),
        "pale": ("Pale", (0.14, 0.14, 0.14)),
        "olive": ("Olive", (-0.03, 0.05, -0.06)),
        "crimson": ("Crimson", (0.10, -0.06, -0.06)),
        "cobalt": ("Cobalt", (-0.07, -0.02, 0.12)),
    }

    def __init__(
        self,
        presets: List[dict] = BASE_3D_PRESETS,
        license_name: str = "CC0-1.0",
        seed: int = 42,
    ) -> None:
        self.presets = presets
        self.license_name = license_name
        self.rng = random.Random(seed)
        self._materials: Dict[str, PBRMaterial3D] = {}
        self._build_base_presets()

    def _make_id(self, signature: str) -> str:
        digest = hashlib.sha1(signature.encode("utf-8")).hexdigest()[:10]
        return f"mat3d_{digest}"

    def _build_base_presets(self) -> None:
        for p in self.presets:
            rgb = hex_to_rgb01(p["base_color_hex"])
            sig = f"base::{p['category']}::{p['name']}"
            mat_id = self._make_id(sig)
            pbr = PBRChannels(
                base_color_hex=p["base_color_hex"].upper(),
                base_color_rgb=rgb,
                metallic=clamp(p.get("metallic", 0.0)),
                roughness=clamp(p.get("roughness", 0.5)),
                ior=p.get("ior", 1.45),
                specular=clamp(p.get("specular", 0.5)),
                clearcoat=clamp(p.get("clearcoat", 0.0)),
                clearcoat_roughness=clamp(p.get("clearcoat_roughness", 0.03)),
                transmission=clamp(p.get("transmission", 0.0)),
                subsurface=clamp(p.get("subsurface", 0.0)),
                subsurface_radius=tuple(p.get("subsurface_radius", (0.8, 0.35, 0.18))),
                sheen=clamp(p.get("sheen", 0.0)),
                normal_strength=p.get("normal_strength", 1.0),
                height_scale=p.get("height_scale", 0.01),
            )
            tags = sorted(set(p.get("ai_tags", []) + [p["category"].lower(), p["subcategory"].lower(), "pbr_3d"]))
            caption = (
                f"{p['name']} 3D PBR material ({p['category']}/{p['subcategory']}), "
                f"metallic={pbr.metallic}, roughness={pbr.roughness}, sss={pbr.subsurface}, "
                f"traits: {', '.join(p.get('surface_traits', []))}."
            )
            self._materials[mat_id] = PBRMaterial3D(
                material_id=mat_id,
                name=p["name"],
                category=p["category"],
                subcategory=p["subcategory"],
                license=self.license_name,
                pbr=pbr,
                required_maps=list(p.get("required_maps", ["basecolor", "normal", "roughness"])),
                surface_traits=list(p.get("surface_traits", [])),
                ai_caption=caption,
                ai_tags=tags,
     