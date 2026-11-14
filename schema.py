from pydantic import BaseModel, Field
from typing import Literal, List, Tuple

class PrimitivePart(BaseModel):
    name: str
    op: Literal["add", "subtract"] = "add"
    kind: Literal["box", "cylinder", "sphere"]
    size: Tuple[float, float, float] = Field(..., description="(width, depth, height) in meters")
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    color_rgba: Tuple[int, int, int, int] = (180, 180, 180, 255)

class SceneSpec(BaseModel):
    asset_name: str
    bounds_max: Tuple[float, float, float] = (5.0, 5.0, 5.0)
    parts: List[PrimitivePart]
    