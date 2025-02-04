from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.dependencies import scoped_session_dependency
from .repositories import LinkRepository
from .service import LinkService


async def link_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)]
):
    return LinkRepository(session)


async def link_service_dependency(repository: Annotated[LinkRepository, Depends(link_repository_dependency)]):
    return LinkService(repository=repository)
