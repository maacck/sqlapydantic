from typing import List
from sqlalchemy import String, VARCHAR, INTEGER
from sqlalchemy.dialects.mysql import TINYTEXT, TINYINT, TINYBLOB
from pydantic import conbytes, conint, constr, confloat, conlist, conset, condecimal, conlist


MAPPER = {
    "TINYTEXT": {"type": "str", "max_length": 255},
    "TINYINT": {"type": "int", "max_length": 4},
    "TINYBLOB": {"type": "str", "max_length": 255},
}
