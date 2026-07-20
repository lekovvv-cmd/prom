from platform_sdk.error_types import InvalidRequest


def parse_if_match(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.startswith("W/"):
        normalized = normalized[2:].strip()
    normalized = normalized.strip('"')
    try:
        version = int(normalized)
    except ValueError as exc:
        raise InvalidRequest("If-Match должен содержать числовую версию ресурса") from exc
    if version < 1:
        raise InvalidRequest("If-Match должен содержать положительную версию ресурса")
    return version
