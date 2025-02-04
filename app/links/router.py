from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    status,
    Depends,
    Path,
    Request,
    HTTPException,
)
from fastapi.responses import (
    RedirectResponse,
    JSONResponse,
    Response,
)
from pydantic import (
    AnyHttpUrl,
    ValidationError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.dependencies import scoped_session_dependency
from .utils import base62_encode
from .repositories import LinkRepository
from .schemas import (
    LinkDTO,
    ShortLinkCreateDTO,
)
from .models import LinkDAO
from .dependencies import link_repository_dependency


router = APIRouter(
    prefix="/l",
    tags=["Links"],
)


@router.post("/shorten/")
async def shorten_link(
    link: ShortLinkCreateDTO,
    repository: Annotated[LinkRepository, Depends(link_repository_dependency)],
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
) -> JSONResponse:
    try:
        url = str(AnyHttpUrl(link.full_url))
        with httpx.Client() as client:
            client.head(url, follow_redirects=True)
    except (ValidationError, httpx.ConnectError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL should be accessible",
        )

    if old_link := await repository.get_by_full_url(link.full_url):
        return JSONResponse(
            content=old_link.model_dump(),
            status_code=status.HTTP_200_OK,
        )
    new_link = LinkDAO(full_url=link.full_url)
    session.add(new_link)
    await session.flush()
    short_url = base62_encode(new_link.id)
    new_link.short_url = short_url
    await session.commit()
    return JSONResponse(
        content=LinkDTO.model_validate(new_link).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{short_url}/")
async def open_link(
    request: Request,
    short_url: Annotated[str, Path],
    repository: Annotated[LinkRepository, Depends(link_repository_dependency)],
) -> Response:
    if request.headers.get("Purpose") == "prefetch":
        return Response()

    if link := await repository.get_by_short_url(short_url):
        await repository.update_by_full_url(
            full_url=link.full_url,
            count_requests=link.count_requests + 1,
        )
        return RedirectResponse(
            url=link.full_url,
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
        )
    return JSONResponse(
        content={"message": "Такой страницы не существует"},
        status_code=status.HTTP_404_NOT_FOUND,
    )
