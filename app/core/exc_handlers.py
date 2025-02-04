from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from .exceptions import ApplicationError
from .schemas import ErrorResponse


if TYPE_CHECKING:
    from fastapi import FastAPI


async def application_exception_handler(ex: ApplicationError) -> JSONResponse:
    return JSONResponse(
        status_code=ex.status_code,
        content=ErrorResponse(
            msg=ex.message,
            code=ex.error_code,
        ).model_dump(mode="json"),
        headers=ex.headers,
    )


def setup_exception_handlers(app: "FastAPI") -> None:
    app.add_exception_handler(ApplicationError, application_exception_handler)  # type: ignore[arg-type]
