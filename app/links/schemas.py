from pydantic import (
    BaseModel,
    ConfigDict,
)


class LinkDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_url: str
    short_url: str
    count_requests: int
    is_active: bool


class ShortLinkCreateDTO(BaseModel):
    full_url: str
