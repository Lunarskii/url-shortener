from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.dependencies import scoped_session_dependency
from .repositories import LinkRepository


async def link_repository_dependency(
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)]
):
    return LinkRepository(session)
