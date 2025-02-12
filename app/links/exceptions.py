from app.core.exceptions import (
    ApplicationError,
    status,
)


class URLNotFoundError(ApplicationError):
    message = "URL not found"
    error_code = "url_not_found"
    status_code = status.HTTP_404_NOT_FOUND


class URLRestricted(ApplicationError):
    message = "URL restricted"
    error_code = "url_restricted"
    status_code = status.HTTP_403_FORBIDDEN


class URLCannotBeEmpty(ApplicationError):
    message = "URL cannot be empty"
    error_code = "url_cannot_be_empty"
    status_code = status.HTTP_400_BAD_REQUEST
