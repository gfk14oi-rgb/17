from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

import numpy as np
import trimesh
from trimesh.smoothing import filter_laplacian, filter_taubin


@dataclass
class JointSpec:
    name: str
    position: Tuple[float, float, float]
    radius: float = 0.09
    kind: str = "sphere"  # "sphere" hoặc "cylinder"
    axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    height: float = 0.14


@dataclass
class CharacterSculptSpec:
    input_glb: str = "output.glb"
    output_glb: str = "character_sculpted.glb"
    joints: List[JointSpec] = None  # type: ignore[assignment]
    sculpt_ops: List[dict] = None  # type: ignore[assignment]
    polish_iterations: int = 4
    polish_mode: str = "taubin"  # "taubin" giữ thể tích tốt hơn, "laplacian" làm mịn nhanh
    gloss: float = 0.65  # 0.0 (lì hoàn toàn) -> 1.0 (bóng gương)
    metallic: float = 0.0  # 0.0 (nhựa/da/vải) -> 1.0 (kim loại)
    base_color_rgba: Tuple[int, int, int, int] = (200, 200, 200, 255)

    def __post_init__(self):
        if self.joints is None:
            self.joints = []
        if self.sculpt_ops is None:
            self.sculpt_ops = []


def connect_joints(mesh: trimesh.Trimesh, joints: List[JointSpec]) -> trimesh.Trimesh:
    """Nối các bộ phận nhân vật bằng các khối khớp tại vị trí chỉ định."""
    if not joints:
        return mesh

    pieces = [mesh]
    for j in joints:
        if j.kind == "cylinder":
            part = trimesh.creation.cylinder(radius=j.radius, height=j.height, sections=24)
            vec = np.array(j.axis, dtype=np.float64)
            if np.linalg.norm(vec) > 0:
                vec = vec / np.linalg.norm(vec)
                align = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], vec)
                part.apply_transform(align)
        else:
            part = trimesh.creation.icosphere(subdivisions=3, radius=j.radius)

        part.apply_translation(j.position)
        pieces.append(part)

    merged = trimesh.util.concatenate(pieces)
    merged.fix_normals()
    return merged


def sculpt_character(mesh: trimesh.Trimesh, ops: List[dict]) -> trimesh.Trimesh:
    """
    Điêu khắc vùng cơ thể cho nhân vật.
    Mỗi phần tử trong ops:
      {"type": "inflate" | "push" | "pinch", "center": [x,y,z], "radius": 0.25, "strength": 0.06, "direction": [0,1,0]}
    """
    if not ops:
        return mesh

    verts = np.asarray(mesh.vertices, dtype=np.float64).copy()
    normals = np.asarray(mesh.vertex_normals, dtype=np.float64)

    for op in ops:
        op_type = op.get("type", "inflate")
        center = np.array(op.get("center", [0.0, 0.0, 0.8]), dtype=np.float64)
        radius = max(float(op.get("radius", 0.25)), 1e-5)
        strength = float(op.get("strength", 0.05))

        dist = np.linalg.norm(verts - center, axis=1)
        weight = np.clip(1.0 - dist / radius, 0.0, 1.0)
        weight = weight * weight * (3.0 - 2.0 * weight)  # smoothstep

        if op_type == "inflate":
            verts += normals * (strength * weight[:, None])
        elif op_type == "push":
            d = np.array(op.get("direction", [0.0, 1.0, 0.0]), dtype=np.float64)
            norm_d = np.linalg.norm(d)
            if norm_d > 0:
                d = d / norm_d
                verts += d[None, :] * (strength * weight[:, None])
        elif op_type == "pinch":
            # Kéo đỉnh vào tâm vùng (tạo hõm, rãnh cơ, khớp)
            to_center = center[None, :] - verts
            verts += to_center * (strength * 0.5 * weight[:, None])

    mesh.vertices = verts
    mesh.fix_normals()
    return mesh


def polish_mesh(
    mesh: trimesh.Trimesh,
    iterations: int = 4,
    mode: str = "taubin",
) -> trimesh.Trimesh:
    """Đánh bóng bề mặt (làm mịn lưới để hết khấc khối)."""
    if iterations <= 0:
        return mesh

    if mode == "laplacian":
        filter_laplacian(mesh, lamb=0.35, iterations=iterations)
    else:
        filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=iterations)

    mesh.fix_normals()
    return mesh


def set_gloss(
    mesh: trimesh.Trimesh,
    gloss: float = 0.65,
    metallic: float = 0.0,
    base_color_rgba: Tuple[int, int, int, int] = (200, 200, 200, 255),
) -> trimesh.Trimesh:
    """
    Chỉnh độ bóng bề mặt cho file xuất .glb.
    gloss: 0.0 (nhám/lì) -> 1.0 (bóng cao)
    """
    gloss_clamped = float(np.clip(gloss, 0.0, 1.0))
    metallic_clamped = float(np.clip(metallic, 0.0, 1.0))
    roughness = round(1.0 - gloss_clamped, 4)

    material = trimesh.visual.material.PBRMaterial(
        baseColorFactor=base_color_rgba,
        roughnessFactor=roughness,
        metallicFactor=metallic_clamped,
    )
    mesh.visual = trimesh.visual.ColorVisuals(mesh=mesh, material=material)
    mesh.visual.face_colors = np.tile(np.array(base_color_rgba, dtype=np.uint8), (len(mesh.faces), 1))
    return mesh


def run_character_pipeline(spec: CharacterSculptSpec) -> dict:
    loaded = trimesh.load(spec.input_glb, force="mesh")
    if isinstance(loaded, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded

    # 1. Nối khớp + điêu khắc + đánh bóng
    mesh = connect_joints(mesh, spec.joints)
    mesh = sculpt_character(mesh, spec.sculpt_ops)
    mesh = polish_mesh(mesh, iterations=spec.polish_iterations, mode=spec.polish_mode)

    # 2. Chỉnh độ bóng & xuất file
    mesh = set_gloss(
        mesh,
        gloss=spec.gloss,
        metallic=spec.metallic,
        base_color_rgba=spec.base_color_rgba,
    )
    mesh.export(spec.output_glb)

    return {
        "ok": True,
        "output_glb": spec.output_glb,
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "gloss": spec.gloss,
        "metallic": spec.metallic,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("USAGE: python character_sculpt.py <config.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        raw = json.load(f)

    joints = [JointSpec(**j) for j in raw.get("joints", [])]
    spec = CharacterSculptSpec(
        input_glb=raw.get("input_glb", "output.glb"),
        output_glb=raw.get("output_glb", "character_sculpted.glb"),
        joints=joints,
        sculpt_ops=raw.get("sculpt_ops", []),
        polish_iterations=int(raw.get("polish_iterations", 4)),
        polish_mode=raw.get("polish_mode", "taubin"),
        gloss=float(raw.get("gloss", 0.65)),
        metallic=float(raw.get("metallic", 0.0)),
        base_color_rgba=tuple(raw.get("base_color_rgba", [200, 200, 200, 255])),
    )
    result = run_character_pipeline(spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
    