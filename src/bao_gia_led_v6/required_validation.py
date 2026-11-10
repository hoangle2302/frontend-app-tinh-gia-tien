"""Requirement rules for finalization; independent from Flet UI and costs.

All seven fields are requirements explicitly supplied by the user. Missing
means None, empty text, or whitespace-only text; string "0" is not blank.
Drafts may be saved incomplete, but completion requires no missing fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from form_schema import HEADER_FIELDS, COMMON_SECTIONS, REQUIRED_FIELDS


@dataclass(frozen=True)
class RequiredIssue:
    key: str
    label: str
    step: int  # 0: configuration, 1: content
    category: str | None = None
    section: str | None = None


def is_filled(value: object) -> bool:
    return value is not None and str(value).strip() != ""


def required_issues(snapshot: dict) -> tuple[RequiredIssue, ...]:
    values = snapshot.get("fields") or {}
    issues: list[RequiredIssue] = []
    for field in HEADER_FIELDS:
        if field.required and not is_filled(values.get(field.key)):
            issues.append(RequiredIssue(field.key, field.label, 0))
    for sec in COMMON_SECTIONS:
        for field in sec.fields:
            if field.required and not is_filled(values.get(field.key)):
                issues.append(RequiredIssue(field.key, field.label, 1, "Thông tin chung", sec.label))
    return tuple(issues)


def required_progress(snapshot: dict, group: str | None = None) -> tuple[int, int]:
    values = snapshot.get("fields") or {}
    if group == "Cấu hình":
        fields = tuple(f for f in HEADER_FIELDS if f.required)
    elif group == "Thông tin chung":
        fields = tuple(f for sec in COMMON_SECTIONS for f in sec.fields if f.required)
    elif group is None:
        fields = REQUIRED_FIELDS
    else:
        raise ValueError(f"Nhóm yêu cầu không xác định: {group}")
    filled = sum(is_filled(values.get(f.key)) for f in fields)
    return filled, len(fields)


def validate_required(snapshot: dict) -> None:
    issues = required_issues(snapshot)
    if issues:
        labels = ", ".join(issue.label for issue in issues)
        raise ValueError(f"Còn thiếu {len(issues)} trường bắt buộc: {labels}")
