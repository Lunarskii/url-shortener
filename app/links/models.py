from typing import Annotated

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database.models import BaseDAO
from app.core.database.mixins import TimestampMixin


class LinkDAO(BaseDAO, TimestampMixin):
    __tablename__ = 'links'

    full_url: Mapped[Annotated[str, mapped_column(unique=True)]]
    short_url: Mapped[Annotated[str, mapped_column(unique=True, nullable=True)]]
    count_requests: Mapped[Annotated[int, mapped_column(default=0)]]
    is_active: Mapped[Annotated[bool, mapped_column(default=True)]]
