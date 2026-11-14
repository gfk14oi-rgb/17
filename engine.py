import trimesh
import numpy as np
from schema import SceneSpec, PrimitivePart

def _build_primitive(part: PrimitivePart) -> trimesh.Trimesh:
    sx, sy, sz = part.size
    if part.kind == "box":
        mesh = trimesh.creation.box(extents=(sx, sy, sz))
    elif part.kind == "cylinder":
        # Trimesh cylinder defaults to Z-axis; rotate so height aligns with Z
        radius = max(sx, sy) / 2.0
        mesh = trimesh.creation.cylinder(radius=radius, height=sz, sections=24)
    elif part.kind == "sphere":
        radius = max(sx, sy, sz) / 2.0
        mesh = trimesh.creation.icosphere(subdivisions=3, radius=radius)
    else:
        raise ValueError(f"Unsupported kind: {part.kind}")

    rx, ry, rz = np.deg2rad(part.rotation_deg)
    rot = trimesh.transformations.euler_matrix(rx, ry, rz, axes="sxyz")
    mesh.apply_transform(rot)
    mesh.apply_translation(part.position)
    mesh.visual.face_colors = part.color_rgba
    return mesh

def compile_and_validate(spec: SceneSpec, out_path: str = "output.glb"):
    errors = []

    if not spec.parts:
        return None, ["Scene has no parts."]

    # 1. Kiểm tra tham số hình học cơ bản
    for p in spec.parts:
        if any(v <= 0 for v in p.size):
            errors.append(f"Part '{p.name}' has non-positive size {p.size}.")
        max_extent = max(abs(x) + s / 2.0 for x, s in zip(p.position, p.size))
        if max_extent > max(spec.bounds_max):
            errors.append(f"Part '{p.name}' exceeds scene bounds {spec.bounds_max}.")

    if errors:
        return None, errors

    # 2. Dựng từng khối
    added = []
    subtracted = []
    for p in spec.parts:
        m = _build_primitive(p)
        if p.op == "add":
            added.append(m)
        else:
            subtracted.append(m)

    if not added:
        return None, ["Scene must have at least one 'add' part."]

    base = trimesh.util.concatenate(added)

    # 3. Kiểm tra chất lượng mesh
    if base.is_empty or len(base.vertices) == 0:
        return None, ["Compiled mesh is empty."]
    if not base.is_watertight:
        errors.append("Warning: Mesh is not watertight (has open gaps/seams).")

    base.export(out_path)
    return out_path, errors
    