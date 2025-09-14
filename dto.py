from typing import Optional

from pydantic import BaseModel


class AssetDto(BaseModel):
    file_id: str
    file_name: str
    url: Optional[str] = None