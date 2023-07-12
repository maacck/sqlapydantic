from sqlalchemy import BIGINT, DateTime, JSON, String, Text
from sqlalchemy.orm import declarative_base, mapped_column
from sqlapydantic import generate_models

Base = declarative_base()


class MPEvent(Base):
    __tablename__ = "mp_event"

    uuid = mapped_column(String(36), primary_key=True)
    topic_name = mapped_column(String(64), nullable=False)
    created_at = mapped_column(DateTime, nullable=False)
    message = mapped_column(Text, nullable=False)
    source_type = mapped_column(String(64))
    source_id = mapped_column(BIGINT)
    source_data = mapped_column(JSON)


def test_strict_types_length():
    result = generate_models([MPEvent], constraint_str_length=True, strict_types=True)
    assert (
        result
        == """from datetime import datetime
from typing import Optional

from pydantic import StrictStr, constr
from pydantic.main import BaseModel


class MPEvent(BaseModel):
    uuid: StrictStr = constr(max_length=36)
    topic_name: StrictStr = constr(max_length=64)
    created_at: StrictStr
    message: StrictStr
    source_type: Optional[StrictStr] = constr(max_length=64)
    source_id: Optional[StrictStr]
    source_data: Optional[StrictStr]
"""
    )


if __name__ == "__main__":
    test_strict_types_length()
