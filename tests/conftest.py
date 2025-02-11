from typing import TYPE_CHECKING

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def pytest_configure(config):
    load_dotenv("tests.env")


@pytest.fixture
async def async_http_client():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
async def urls(shared_datadir) -> list[str]:
    contents = (shared_datadir / "urls.txt").read_text()
    return contents.splitlines()


@pytest.fixture
async def db_session() -> "AsyncSession":
    from app.core.database.connection import async_session_factory

    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="package", autouse=True)
async def db_lifespan() -> None:
    from app.core.database.connection import async_engine
    from app.core.database.models import BaseModel
    from app.links.models import LinkDAO

    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
