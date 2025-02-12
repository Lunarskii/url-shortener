from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class LinkDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(exclude=True, default=-1)]
    full_url: str
    short_url: str
    count_requests: int
    is_active: bool


class ShortLinkCreateDTO(BaseModel):
    full_url: str
