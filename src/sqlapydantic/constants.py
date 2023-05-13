from pydantic import conbytes, conint, constr, confloat, conlist, conset, condecimal, conlist

MYSQL_TINYTEXT = constr(max_length=255)
MYSQL_TINYINT = conint(gt=0, le=255)
MYSQL_TINYBLOB = conbytes(max_length=255)
