from typing import Any

from sqlalchemy import select

from app.core.database.repositories import BaseAlchemyRepository
from .models import LinkDAO
from .schemas import LinkDTO


class LinkRepository(BaseAlchemyRepository[LinkDAO, LinkDTO]):
    model_type = LinkDAO
    schema_type = LinkDTO

    async def get_by_full_url(self, full_url: str) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.full_url == full_url) # noqa
        result = await self.session.scalar(stmt)
        if result is None:
            return None
        return self.schema_type.model_validate(result)

    async def get_by_short_url(self, short_url: str) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.short_url == short_url) # noqa
        result = await self.session.scalar(stmt)
        if result is None:
            return None
        return self.schema_type.model_validate(result)

    async def update_by_full_url(self, full_url: str, **data: Any) -> LinkDTO | None:
        stmt = select(self.model_type).where(self.model_type.full_url == full_url) # noqa
        instances = await self.session.execute(stmt)
        instance = instances.scalar()
        if instance is None:
            return None
        instance.update(**data)
        await self.session.commit()
        return self.schema_type.model_validate(instance)
