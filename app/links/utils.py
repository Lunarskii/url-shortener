import string
from typing import LiteralString


BASE62: LiteralString = string.ascii_letters + string.digits
BASE62_LEN: int = len(BASE62)


def base62_encode(num: int) -> str:
    result = []
    while num > 0:
        num, rem = divmod(num, BASE62_LEN)
        result.append(BASE62[rem])
    return ''.join(reversed(result)).zfill(6)
