from typing import Any
from app.core.database import db


class BaseRepository:
    def __init__(self, table: str):
        self.table = table
        self.db = db

    async def get_by_id(self, record_id: str) -> dict | None:
        rows = await self.db.select(self.table, {"select": "*", "id": f"eq.{record_id}", "limit": "1"})
        return rows[0] if rows else None

    async def list_all(self, params: dict | None = None) -> list[dict]:
        return await self.db.select(self.table, params or {"select": "*"})

    async def create(self, payload: dict) -> dict:
        rows = await self.db.insert(self.table, payload)
        return rows[0]

    async def update(self, filter_params: dict, payload: dict) -> list[dict]:
        return await self.db.patch(self.table, filter_params, payload)
