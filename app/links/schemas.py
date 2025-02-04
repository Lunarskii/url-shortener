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

    # @field_validator("full_url", mode="before")
    # @classmethod
    # def validate_url(cls, value: Any) -> Any:
    #     url = str(AnyHttpUrl(value))
    #     try:
    #         with httpx.Client() as client:
    #             client.head(url, follow_redirects=True)
    #     except httpx.ConnectError:
    #         raise ValidationError("URL should be accessible")
    #     return url
