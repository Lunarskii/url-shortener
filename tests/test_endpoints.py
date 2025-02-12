import pytest
from fastapi import status
from httpx import Response

from app.links.exceptions import (
    URLNotFoundError,
    URLRestricted,
    URLCannotBeEmpty,
)


def assert_any_exception(exctype, response: Response):
    assert response.status_code == exctype.status_code
    response_json = response.json()
    assert response_json.get("msg") == exctype.message
    assert response_json.get("code") == exctype.error_code


@pytest.mark.order(1)
@pytest.mark.asyncio(loop_scope="session")
async def test__shorten_url(async_http_client, urls):
    for url in urls:
        response = await async_http_client.post(url="/l/shorten/", json={"full_url": url})
        assert response.status_code in [status.HTTP_200_OK, URLRestricted.status_code, URLCannotBeEmpty.status_code]
        response_json = response.json()
        if response.status_code == status.HTTP_200_OK:
            full_url: str = response_json.get("full_url")
            assert full_url == url or full_url == f"http://{url}" or full_url == f"https://{url}"
            assert response_json.get("short_url") is not None
            assert response_json.get("count_requests") == 0
            assert response_json.get("is_active") is True
        elif response.status_code == URLRestricted.status_code:
            assert_any_exception(URLRestricted, response)
        else:
            assert_any_exception(URLCannotBeEmpty, response)


@pytest.mark.order(4)
@pytest.mark.asyncio(loop_scope="session")
async def test__shorten_url__restricted_url(async_http_client):
    response = await async_http_client.post(
        url="/l/shorten/",
        json={"full_url": "http://eritreandiaspora.org/"},
    )
    assert_any_exception(URLRestricted, response)


@pytest.mark.order(3)
@pytest.mark.asyncio(loop_scope="session")
async def test__deactivate_link(async_http_client):
    short_url = "00000r"
    response = await async_http_client.get(url=f"/l/{short_url}/deactivate/")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json.get("full_url") == "http://eritreandiaspora.org/"
    assert response_json.get("short_url") == short_url
    assert response_json.get("is_active") is False


@pytest.mark.asyncio(loop_scope="session")
async def test__deactivate_link__unknown_url(async_http_client):
    response = await async_http_client.get(url=f"/l/XXXXXX/deactivate/")
    assert_any_exception(URLNotFoundError, response)


@pytest.mark.order(2)
@pytest.mark.asyncio(loop_scope="session")
async def test__open_link(async_http_client):
    short_url = "00000r"
    response = await async_http_client.get(url=f"/l/{short_url}/")
    assert response.status_code == status.HTTP_308_PERMANENT_REDIRECT
    response_redirect = await async_http_client.get(url=f"/l/{short_url}/", follow_redirects=True)
    assert response_redirect.status_code == status.HTTP_200_OK
    assert response_redirect.url == "https://eritreandiaspora.org/"


@pytest.mark.order(5)
@pytest.mark.asyncio(loop_scope="session")
async def test__open_link__restricted_url(async_http_client):
    response = await async_http_client.get(url="/l/00000r/")
    assert_any_exception(URLRestricted, response)


@pytest.mark.asyncio(loop_scope="session")
async def test__open_link__unknown_url(async_http_client):
    response = await async_http_client.get(url="/l/XXXXXX/")
    assert_any_exception(URLNotFoundError, response)


@pytest.mark.order(6)
@pytest.mark.asyncio(loop_scope="session")
async def test__activate_link(async_http_client):
    short_url = "00000r"
    response = await async_http_client.get(url=f"/l/{short_url}/activate/")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json.get("full_url") == "http://eritreandiaspora.org/"
    assert response_json.get("short_url") == short_url
    assert response_json.get("is_active") is True


@pytest.mark.asyncio(loop_scope="session")
async def test__activate_link__unknown_url(async_http_client):
    response = await async_http_client.get(url=f"/l/XXXXXX/activate/")
    assert_any_exception(URLNotFoundError, response)
