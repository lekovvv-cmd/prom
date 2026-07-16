from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any

from app.core.enums import TemplateFieldType
from app.modules.templates.models import ServiceDeskTemplateField, ServiceDeskTemplateVersion
from app.modules.templates.schemas import TemplateValidationErrorItem, TemplateValidationResult


def validate_template_payload(
    version: ServiceDeskTemplateVersion,
    data: dict[str, Any],
    *,
    dictionary_options: dict[str, set[Any]] | None = None,
) -> TemplateValidationResult:
    fields = sorted(version.fields, key=lambda field: (field.position, field.label))
    visible_fields = [field for field in fields if _matches_rules(field.visibility_rules, data, default=True)]
    visible_keys = [field.key for field in visible_fields]
    required_fields = [
        field
        for field in visible_fields
        if field.is_required or _matches_rules(field.required_rules, data, default=False)
    ]
    required_keys = [field.key for field in required_fields]

    errors: list[TemplateValidationErrorItem] = []
    normalized_data: dict[str, Any] = {}

    for field in visible_fields:
        value = data.get(field.key)
        if _is_empty(value):
            if field.key in required_keys:
                errors.append(_error(field, "Заполните обязательное поле"))
            continue

        normalized_data[field.key] = value
        errors.extend(_validate_field_value(field, value, dictionary_options=dictionary_options))

    return TemplateValidationResult(
        is_valid=not errors,
        errors=errors,
        visible_fields=visible_keys,
        required_fields=required_keys,
        normalized_data=normalized_data,
    )


def _validate_field_value(
    field: ServiceDeskTemplateField,
    value: Any,
    *,
    dictionary_options: dict[str, set[Any]] | None = None,
) -> list[TemplateValidationErrorItem]:
    errors: list[TemplateValidationErrorItem] = []
    rules = field.validation or {}

    if field.field_type in {TemplateFieldType.TEXT, TemplateFieldType.TEXTAREA, TemplateFieldType.RICH_TEXT}:
        if not isinstance(value, str):
            return [_error(field, "Укажите текстовое значение")]
        errors.extend(_validate_string_rules(field, value, rules))

    if field.field_type == TemplateFieldType.EMAIL:
        if not isinstance(value, str) or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            errors.append(_error(field, "Укажите корректный email"))
        elif rules.get("email") is True:
            errors.extend(_validate_string_rules(field, value, rules))

    if field.field_type == TemplateFieldType.NUMBER:
        number = _to_number(value)
        if number is None:
            errors.append(_error(field, "Укажите число"))
        else:
            min_value = rules.get("min")
            max_value = rules.get("max")
            if min_value is not None and number < float(min_value):
                errors.append(_error(field, f"Значение должно быть не меньше {min_value}"))
            if max_value is not None and number > float(max_value):
                errors.append(_error(field, f"Значение должно быть не больше {max_value}"))

    if field.field_type in {TemplateFieldType.DATE, TemplateFieldType.DATETIME}:
        parsed = _parse_date(value)
        if parsed is None:
            errors.append(_error(field, "Укажите дату в формате YYYY-MM-DD"))
        else:
            min_date = _parse_date(rules.get("min_date"))
            max_date = _parse_date(rules.get("max_date"))
            if min_date and parsed < min_date:
                errors.append(_error(field, f"Дата должна быть не раньше {min_date.isoformat()}"))
            if max_date and parsed > max_date:
                errors.append(_error(field, f"Дата должна быть не позже {max_date.isoformat()}"))

    if field.field_type == TemplateFieldType.TIME and _parse_time(value) is None:
        errors.append(_error(field, "Укажите время в формате HH:MM"))

    if field.field_type == TemplateFieldType.SELECT:
        allowed_values = _option_values(field, dictionary_options)
        if allowed_values is not None and value not in allowed_values:
            errors.append(_error(field, "Выберите значение из списка"))

    if field.field_type == TemplateFieldType.MULTISELECT:
        if not isinstance(value, list):
            errors.append(_error(field, "Выберите одно или несколько значений"))
        else:
            allowed_values = _option_values(field, dictionary_options)
            if allowed_values is not None and any(item not in allowed_values for item in value):
                errors.append(_error(field, "Выберите значения из списка"))

    if field.field_type == TemplateFieldType.CHECKBOX and not isinstance(value, bool):
        errors.append(_error(field, "Укажите да или нет"))

    if field.field_type == TemplateFieldType.FILE:
        files = value if isinstance(value, list) else [value]
        max_files = rules.get("max_files")
        if max_files is not None and len(files) > int(max_files):
            errors.append(_error(field, f"Можно приложить не больше {max_files} файлов"))
        allowed_extensions = rules.get("allowed_extensions")
        if allowed_extensions:
            normalized_extensions = {str(item).lower().lstrip(".") for item in allowed_extensions}
            for file_item in files:
                file_name = file_item.get("name") if isinstance(file_item, dict) else str(file_item)
                extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
                if extension not in normalized_extensions:
                    errors.append(_error(field, "Недопустимый формат файла"))
                    break

    return errors


def _validate_string_rules(
    field: ServiceDeskTemplateField,
    value: str,
    rules: dict[str, Any],
) -> list[TemplateValidationErrorItem]:
    errors: list[TemplateValidationErrorItem] = []
    min_length = rules.get("min_length")
    max_length = rules.get("max_length")
    regex = rules.get("regex")
    if min_length is not None and len(value) < int(min_length):
        errors.append(_error(field, f"Введите минимум {min_length} символов"))
    if max_length is not None and len(value) > int(max_length):
        errors.append(_error(field, f"Введите не больше {max_length} символов"))
    if regex and not re.match(str(regex), value):
        errors.append(_error(field, "Значение не соответствует формату"))
    return errors


def _matches_rules(rules: Any, data: dict[str, Any], *, default: bool) -> bool:
    if not rules:
        return default
    if isinstance(rules, list):
        return all(_matches_rule(rule, data) for rule in rules)
    if isinstance(rules, dict):
        return _matches_rule(rules, data)
    return default


def _matches_rule(rule: dict[str, Any], data: dict[str, Any]) -> bool:
    field = str(rule.get("field", ""))
    operator = rule.get("operator", "equals")
    expected = rule.get("value")
    actual = data.get(field)
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "in":
        return actual in (expected or [])
    if operator == "not_in":
        return actual not in (expected or [])
    if operator == "is_empty":
        return _is_empty(actual)
    if operator == "is_not_empty":
        return not _is_empty(actual)
    return False


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _to_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None


def _parse_time(value: Any) -> time | None:
    if isinstance(value, time):
        return value
    if not isinstance(value, str):
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        return None


def _option_values(
    field: ServiceDeskTemplateField,
    dictionary_options: dict[str, set[Any]] | None = None,
) -> set[Any] | None:
    if field.dictionary_code:
        return (dictionary_options or {}).get(field.dictionary_code, set())
    if field.options is None:
        return None
    return {item.get("value") for item in field.options if isinstance(item, dict) and "value" in item}


def _error(field: ServiceDeskTemplateField, message: str) -> TemplateValidationErrorItem:
    return TemplateValidationErrorItem(field_key=field.key, message=f"{field.label}: {message}")
