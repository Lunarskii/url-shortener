from typing import Annotated
from datetime import (
    datetime,
    UTC,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)


def local_time() -> datetime:
    return datetime.now()


def universal_time() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class IDMixin:
    __abstract__ = True

    id: Mapped[Annotated[int, mapped_column(primary_key=True, sort_order=-100)]]


class TimestampMixin:
    __abstract__ = True

    created_at: Mapped[
        Annotated[
            datetime,
            mapped_column(default=universal_time, sort_order=100),
        ]
    ]
    updated_at: Mapped[
        Annotated[
            datetime,
            mapped_column(default=universal_time, onupdate=universal_time, sort_order=101),
        ]
    ]
