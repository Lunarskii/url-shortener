from typing import Annotated

from fastapi import (
    APIRouter,
    status,
    Depends,
    Path,
    Request,
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


@router.post("/shorten/", status_code=status.HTTP_200_OK)
async def shorten_link(
    link: ShortLinkCreateDTO,
    session: Annotated[AsyncSession, Depends(scoped_session_dependency)],
    service: Annotated[LinkService, Depends(link_service_dependency)],
) -> LinkDTO:
    return await service.shorten_url(link, session)


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
