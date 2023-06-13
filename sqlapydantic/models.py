from typing import Optional, List, Set

from pydantic import BaseModel



class ColumnAttribute(BaseModel):
    optional: Optional[bool]
    key: str
    type_hint: str

class ModelClass(BaseModel):
    name: str
    columns: List["ColumnAttribute"]
    readonly_fields: Set[str]
    create_only_fields: Set[str]