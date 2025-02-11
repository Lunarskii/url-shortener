from typing import Any

from sqlalchemy import select

from app.core.database.repositories import BaseAlchemyRepository
from .models import LinkDAO
from .schemas import LinkDTO


class LinkRepository(BaseAlchemyRepository[LinkDAO, LinkDTO]):
    model_type = LinkDAO
    schema_type = LinkDTO

    async def flush_create(self, **data: Any):
        instance = LinkDAO(**{key: value for key, value in data.items() if not callable(value)})
        self.session.add(instance)
        await self.session.flush()
        instance.update(**{key: value(instance.id) for key, value in data.items() if callable(value)})
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def get_by_full_url(self, full_url: str) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.full_url == full_url)  # noqa
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)

    async def get_by_short_url(self, short_url: str) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.short_url == short_url)  # noqa
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)

    async def update_by_full_url(self, full_url: str, **data: Any) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.full_url == full_url)  # noqa
        instance = await self.session.scalar(stmt)
        if instance is None:
            return None
        instance.update(**data)
        await self.session.commit()
        return self.schema_type.model_validate(instance)
