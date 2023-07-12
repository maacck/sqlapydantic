from typing import Any, List, Optional, Set

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.orm import DeclarativeBase


class ColumnAttribute(BaseModel):
    orm_column: Optional[Column]
    optional: Optional[bool]
    key: str
    python_type: str
    is_relationship: Optional[bool] = False

    class Config:
        arbitrary_types_allowed = True


class ModelClass(BaseModel):
    name: str
    columns: List["ColumnAttribute"]
    parent_class: Optional[Any] = None
    relationship_classes: Optional[List[Any]] = []


class CustomDeclarativeBase(DeclarativeBase):
    __readonly_fields__: Set[str] = None
    __create_only_fields__: Set[str] = None
    __split_models__: bool = None
