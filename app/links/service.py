import httpx
from pydantic import (
    AnyHttpUrl,
    ValidationError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .models import LinkDAO
from .repositories import LinkRepository
from .schemas import (
    ShortLinkCreateDTO,
    LinkDTO,
)
from .utils import base62_encode
from .exceptions import (
    URLMustBeAccessibleError,
    URLRestricted,
)


async def validate_url_access(url: str) -> bool:
    try:
        url = str(AnyHttpUrl(url))
        async with httpx.AsyncClient() as client:
            await client.head(url, follow_redirects=True)
    except (ValidationError, httpx.ConnectError):
        return False
    return True


class LinkService:
    def __init__(
        self,
        session: AsyncSession | None = None,
        repository: LinkRepository | None = None,
    ):
        if repository:
            self.repository = repository
        elif session:
            self.repository = LinkRepository(session)
        else:
            raise ValueError("A session or repository is required. None of them are defined.")

    async def shorten_url(self, link: ShortLinkCreateDTO, session: AsyncSession) -> LinkDTO:
        if not validate_url_access(link.full_url):
            raise URLMustBeAccessibleError()

        if old_link := await self.repository.get_by_full_url(link.full_url):
            if not old_link.is_active:
                raise URLRestricted()
            return old_link
        else:
            new_link = LinkDAO(full_url=link.full_url)
            session.add(new_link)
            await session.flush()
            short_url = base62_encode(new_link.id)
            new_link.short_url = short_url
            await session.commit()
            return LinkDTO.model_validate(new_link)

    async def get_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            if not link.is_active:
                raise URLRestricted()
            await self.repository.update_by_full_url(
                full_url=link.full_url,
                count_requests=link.count_requests + 1,
            )
            return link
        return None

    async def deactivate_link(self, short_url: str):
        if link := await self.repository.get_by_short_url(short_url):
            await self.repository.update(link.id, is_active=False)

    async def activate_link(self, short_url: str):
        if link := await self.repository.get_by_short_url(short_url):
            await self.repository.update(link.id, is_active=True)

    async def get_links(self, is_active: bool | None = None) -> list[LinkDTO]:
        if is_active is not None:
            return await self.repository.get_all(is_active=is_active)
        return await self.repository.get_all()
