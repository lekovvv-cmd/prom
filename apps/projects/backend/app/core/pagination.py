DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(1, min(limit, MAX_LIMIT))


def clamp_offset(offset: int | None) -> int:
    if offset is None:
        return 0
    return max(0, offset)
