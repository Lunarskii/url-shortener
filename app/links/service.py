from typing import Literal

import httpx
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
    def _normalize_url(
        cls,
        url: str,
        protocol: Literal["http", "https"] = "https",
    ) -> str:
        if not url.startswith(("http://", "https://")):
            url = f"{protocol}://{url}"
        return url

    @classmethod
    def _change_url_protocol(
        cls,
        url: str,
        protocol: Literal["http", "https"] = "https",
    ) -> str:
        if url.startswith("http://") and protocol == "https":
            url = url.replace("http", protocol, 1)
        elif url.startswith("https://") and protocol == "http":
            url = url.replace("https", protocol, 1)
        return url

    @classmethod
    async def _validate_url(cls, url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
                await client.head(url)
        except (httpx.ConnectError, httpx.UnsupportedProtocol, httpx.ConnectTimeout):
            return False
        return True

    async def shorten_url(self, link: ShortLinkCreateDTO, session: AsyncSession) -> LinkDTO:
        url = self._normalize_url(link.full_url, "http")
        if not await self._validate_url(url):
            url = self._change_url_protocol(url, "https")
            if not await self._validate_url(url):
                raise URLMustBeAccessibleError()

        if old_link := await self.repository.get_by_full_url(url):
            if not old_link.is_active:
                raise URLRestricted()
            return old_link
        else:
            new_link = LinkDAO(full_url=url)
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

    async def deactivate_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            return await self.repository.update(link.id, is_active=False)

    async def activate_link(self, short_url: str) -> LinkDTO | None:
        if link := await self.repository.get_by_short_url(short_url):
            return await self.repository.update(link.id, is_active=True)

    async def get_links(self, is_active: bool | None = None) -> list[LinkDTO]:
        if is_active is not None:
            return await self.repository.get_all(is_active=is_active)
        return await self.repository.get_all()
