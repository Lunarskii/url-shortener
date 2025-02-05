from typing import Annotated

from fastapi import (
    APIRouter,
    status,
    Depends,
    Path,
    Request,
    Query,
)
from fastapi.responses import (
    RedirectResponse,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.dependencies import scoped_session_dependency
from .service import LinkService
from .schemas import (
    LinkDTO,
    ShortLinkCreateDTO,
)
from .dependencies import link_service_dependency
from .exceptions import URLNotFoundError


router = APIRouter(
    prefix="/l",
    tags=["Links"],
)


@router.post("/shorten/")
async def shorten_link(
    link: ShortLinkCreateDTO,
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
    service: Annotated[LinkService, Depends(link_service_dependency)],
) -> LinkDTO:
    return await service.shorten_url(link, session)


@router.get("/list/")
async def get_links(
    service: Annotated[LinkService, Depends(link_service_dependency)],
    is_active: Annotated[bool | None, Query] = None,
) -> list[LinkDTO]:
    return await service.get_links(is_active)


@router.get("/{short_url}/deactivate/")
async def deactivate_link(
    short_url: Annotated[str, Path],
    service: Annotated[LinkService, Depends(link_service_dependency)],
) -> None:
    await service.deactivate_link(short_url)


@router.get("/{short_url}/activate/")
async def activate_link(
    short_url: Annotated[str, Path],
    service: Annotated[LinkService, Depends(link_service_dependency)],
) -> None:
    await service.activate_link(short_url)


@router.get("/{short_url}/")
async def open_link(
    request: Request,
    short_url: Annotated[str, Path],
    service: Annotated[LinkService, Depends(link_service_dependency)],
) -> Response:
    if request.headers.get("Purpose") == "prefetch":
        return Response()

    if link := await service.get_link(short_url):
        return RedirectResponse(
            url=link.full_url,
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
        )
    raise URLNotFoundError()
