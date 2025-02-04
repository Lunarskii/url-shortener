from abc import ABC
from typing import Any

from sqlalchemy import (
    select,
    Result,
)
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .models import BaseDAO


class BaseAlchemyRepository[M: BaseDAO, S: BaseModel](ABC):
    session: AsyncSession
    model_type: type[M]
    schema_type: type[S]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **data: Any) -> S:
        instance = self.model_type(**data)
        self.session.add(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def get(self, id_: int) -> S | None:
        instance = await self.session.get(self.model_type, id_)
        if instance is None:
            return None
        return self.schema_type.model_validate(instance)

    async def get_all(self) -> list[S]:
        stmt = select(self.model_type)
        result: Result = await self.session.execute(stmt)
        instances = result.scalars().all()
        return [self.schema_type.model_validate(instance) for instance in instances]

    async def update(self, id_: int, **data: Any) -> S:
        instance = await self.session.get_one(self.model_type, id_)
        instance.update(**data)
        await self.session.commit()
        return self.schema_type.model_validate(instance)

    async def delete(self, id_: int) -> S:
        instance = await self.session.get_one(self.model_type, id_)
        await self.session.delete(instance)
        await self.session.commit()
        return self.schema_type.model_validate(instance)
