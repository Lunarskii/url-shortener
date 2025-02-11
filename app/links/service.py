from sqlalchemy.ext.asyncio import AsyncSession

from .repositories import LinkRepository
from .schemas import (
    ShortLinkCreateDTO,
    LinkDTO,
)
from .utils import base62_encode
from .exceptions import (
    URLRestricted,
    URLNotFoundError,
)


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

    @classmethod
    def _normalize_url(cls, url: str) -> str:
        if not url.startswith("http"):
            url = f"http://{url}"
        return url

    async def shorten_url(self, link: ShortLinkCreateDTO) -> LinkDTO:
        url = self._normalize_url(link.full_url)
        if old_link := await self.repository.get_by_full_url(url):
            if not old_link.is_active:
                raise URLRestricted()
            return old_link
        else:
            return await self.repository.flush_create(full_url=url, short_url=base62_encode)

    async def get_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            if not link.is_active:
                raise URLRestricted()
            link = await self.repository.update_by_full_url(
                full_url=link.full_url,
                count_requests=link.count_requests + 1,
            )
            return link
        raise URLNotFoundError()

    async def deactivate_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            return await self.repository.update(link.id, is_active=False)
        raise URLNotFoundError()

    async def activate_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            return await self.repository.update(link.id, is_active=True)
        raise URLNotFoundError()

    async def get_links(self, is_active: bool | None = None) -> list[LinkDTO]:
        if is_active is not None:
            return await self.repository.get_all(is_active=is_active)
        return await self.repository.get_all()
