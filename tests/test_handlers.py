import random
import string
from typing import Literal

import pytest

from app.links.service import LinkService
from app.links.schemas import (
    ShortLinkCreateDTO,
    LinkDTO,
)
from app.links.exceptions import (
    URLNotFoundError,
    URLRestricted,
    URLCannotBeEmpty,
)


def assert_any_exception(exctype, excinfo):
    assert excinfo.type is exctype
    assert excinfo.value.message == exctype.message
    assert excinfo.value.error_code == exctype.error_code
    assert excinfo.value.status_code == exctype.status_code


def generate_random_string(length: int = 16) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def generate_random_url(length: int = 16, protocol: Literal["http", "https"] | None = None) -> str:
    random_string: str = generate_random_string(length)
    if protocol:
        return f"{protocol}://{random_string}"
    return f"{random.choice(["http", "https"])}://{random_string}"


def assert_link_dto(
    dto: LinkDTO,
    full_url: str,
    short_url: str | None = None,
    count_requests: int = 0,
    is_active: bool = True,
    *,
    short_url_length: int = 6,
    short_url_alphabet: str = string.ascii_letters + string.digits,
) -> None:
    assert dto
    assert dto.full_url == full_url
    assert len(dto.short_url) == short_url_length
    assert all(ch in short_url_alphabet for ch in dto.short_url)
    if short_url:
        assert dto.short_url == short_url
    else:
        assert dto.short_url
    assert dto.count_requests == count_requests
    assert dto.is_active is is_active


@pytest.mark.asyncio(loop_scope="session")
class TestLinkService:
    link_service: LinkService = None

    @classmethod
    @pytest.fixture(autouse=True)
    async def setup_link_service(cls, db_session):
        cls.link_service = LinkService(session=db_session)

    async def shorten_url(
        self,
        protocol: Literal["http", "https"] = "http",
        *,
        url: str | None = None,
    ) -> LinkDTO:
        if not url:
            url = generate_random_url(protocol=protocol)
        link = ShortLinkCreateDTO(full_url=url)
        shorten_url_result: LinkDTO = await self.link_service.shorten_url(link)
        assert_link_dto(
            dto=shorten_url_result,
            full_url=url,
        )
        return shorten_url_result

    async def deactivate_link(
        self,
        protocol: Literal["http", "https"] = "http",
        *,
        url: str | None = None,
    ) -> LinkDTO:
        link = await self.get_link(protocol=protocol, url=url, use_service=False)
        deactivate_link_result = await self.link_service.deactivate_link(link.short_url)
        assert_link_dto(
            dto=deactivate_link_result,
            full_url=link.full_url,
            short_url=link.short_url,
            count_requests=link.count_requests,
            is_active=False,
        )
        return deactivate_link_result

    async def activate_link(
        self,
        protocol: Literal["http", "https"] = "http",
        *,
        url: str | None = None,
    ) -> LinkDTO:
        link = await self.get_link(protocol=protocol, url=url, use_service=False)
        activate_link_result = await self.link_service.activate_link(link.short_url)
        assert_link_dto(
            dto=activate_link_result,
            full_url=link.full_url,
            short_url=link.short_url,
            count_requests=link.count_requests,
            is_active=True,
        )
        return activate_link_result

    async def get_link(
        self,
        protocol: Literal["http", "https"] = "http",
        *,
        url: str | None = None,
        use_service: bool = True,
    ) -> LinkDTO:
        if not url:
            shorten_url_result = await self.shorten_url(protocol=protocol)
            full_url = shorten_url_result.full_url
            short_url = shorten_url_result.short_url
            count_requests = shorten_url_result.count_requests
            is_active = shorten_url_result.is_active
        else:
            link = await self.link_service.repository.get_by_full_url(full_url=url)
            full_url = link.full_url
            short_url = link.short_url
            count_requests = link.count_requests
            is_active = link.is_active
        if use_service:
            get_link_result: LinkDTO = await self.link_service.get_link(short_url)
            assert_link_dto(
                dto=get_link_result,
                full_url=full_url,
                short_url=short_url,
                count_requests=count_requests + 1,
            )
            return get_link_result
        return LinkDTO(
            full_url=full_url,
            short_url=short_url,
            count_requests=count_requests,
            is_active=is_active,
        )

    async def test__normalize_url__with_protocol(self):
        http_url = generate_random_url(protocol="http")
        https_url = generate_random_url(protocol="https")
        assert self.link_service._normalize_url(http_url) == http_url
        assert self.link_service._normalize_url(https_url) == https_url

    async def test__normalize_url__without_protocol(self):
        url_without_protocol = generate_random_string()
        assert self.link_service._normalize_url(url_without_protocol) == f"http://{url_without_protocol}"

    async def test__shorten_url__without_protocol(self):
        url_without_protocol = generate_random_string()
        link = ShortLinkCreateDTO(full_url=url_without_protocol)
        func_result: LinkDTO = await self.link_service.shorten_url(link)
        assert_link_dto(
            dto=func_result,
            full_url=f"http://{url_without_protocol}",
        )

    async def test__shorten_url__with_protocol(self):
        await self.shorten_url(protocol="http")
        await self.shorten_url(protocol="https")

    async def test__shorten_url__existing_url(self):
        shorten_url_result = await self.shorten_url(protocol="http")
        shorten_url_result_2: LinkDTO = await self.shorten_url(url=shorten_url_result.full_url)
        assert_link_dto(
            dto=shorten_url_result_2,
            full_url=shorten_url_result.full_url,
            short_url=shorten_url_result.short_url,
            count_requests=shorten_url_result.count_requests,
            is_active=shorten_url_result.is_active,
        )

    async def test__shorten_url__restricted_url(self):
        deactivate_link_result = await self.deactivate_link(protocol="http")
        with pytest.raises(URLRestricted) as exc:
            await self.shorten_url(url=deactivate_link_result.full_url)
        assert_any_exception(URLRestricted, exc)

    async def test__shorten_url__empty_url(self):
        with pytest.raises(URLCannotBeEmpty) as exc:
            await self.link_service.shorten_url(ShortLinkCreateDTO(full_url=""))
        assert_any_exception(URLCannotBeEmpty, exc)

    async def test__get_link(self):
        await self.get_link(protocol="http")

    async def test__get_link__restricted_url(self):
        deactivate_link_result = await self.deactivate_link(protocol="http")
        with pytest.raises(URLRestricted) as exc:
            await self.get_link(url=deactivate_link_result.full_url)
        assert_any_exception(URLRestricted, exc)

    async def test__get_link__unknown_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.get_link("XXXXXX")
        assert_any_exception(URLNotFoundError, exc)

    async def test__get_link__empty_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.get_link("")
        assert_any_exception(URLNotFoundError, exc)

    async def test__deactivate_link(self):
        await self.deactivate_link(protocol="http")

    async def test__deactivate_link__unknown_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.deactivate_link("XXXXXX")
        assert_any_exception(URLNotFoundError, exc)

    async def test__deactivate_link__empty_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.deactivate_link("")
        assert_any_exception(URLNotFoundError, exc)

    async def test__activate_link(self):
        await self.activate_link(protocol="http")

    async def test__activate_link__deactivated_link(self):
        deactivate_link_result = await self.deactivate_link(protocol="http")
        await self.activate_link(url=deactivate_link_result.full_url)

    async def test__activate_link__unknown_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.activate_link("XXXXXX")
        assert_any_exception(URLNotFoundError, exc)

    async def test__activate_link__empty_url(self):
        with pytest.raises(URLNotFoundError) as exc:
            await self.link_service.activate_link("")
        assert_any_exception(URLNotFoundError, exc)
