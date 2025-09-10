from typing import Optional

from pydantic import BaseModel


class AssetDto(BaseModel):
    data: Optional[bytes] = None
    url: Optional[str] = None