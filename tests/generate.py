from sqlalchemy import BIGINT, DateTime, String, Text
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


def generate_from_module():
    result = generate_models([MPEvent])
    assert (
        result
        == """from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel


class MPEvent(BaseModel):
    uuid: str
    topic_name: str
    created_at: datetime
    message: str
    source_type: Optional[str]
    source_id: Optional[int]
"""
    )


if __name__ == "__main__":
    generate_from_module()
