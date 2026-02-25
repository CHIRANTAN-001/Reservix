import enum


class TTL(str, enum.Enum):
    TEN_MINUTES = 60 * 10
    ONE_MINUTE = 60 * 1
    TEN_SECOND = 10