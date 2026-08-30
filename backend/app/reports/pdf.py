"""Dependency-free PDF output for the compact assessment report."""

import json
from collections.abc import Iterable
from textwrap import wrap


def render_assessment_pdf(report: dict) -> bytes:
    """Render a readable text report as a valid PDF 1.4 document."""

    lines: list[str] = [
        "GenomixAI Medication Assessment Report",
        "SYNTHETIC/DEMO DATA - NOT CLINICALLY VALIDATED" if report["synthetic_data"] else "",
        "",
    ]
    lines.extend(_json_lines(report))
    pages = [lines[index : index + 46] for index in range(0, len(lines), 46)] or [[]]
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids: list[int] = []
    for page_number, page_lines in enumerate(pages, start=1):
        content = _content_stream(page_lines, page_number, len(pages))
        content_id = len(objects) + 1
        objects.append(
            b"<< /Length "
            + str(len(content)).encode()
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = len(objects) + 1
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 3 0 R >> >> /Contents "
            + str(content_id).encode()
            + b" 0 R >>"
        )
        page_ids.append(page_id)
    objects[1] = (
        b"<< /Type /Pages /Count "
        + str(len(page_ids)).encode()
        + b" /Kids ["
        + b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
        + b"] >>"
    )
    return _pdf_document(objects)


def _json_lines(report: dict) -> list[str]:
    serialized = json.dumps(report, indent=2, default=str, ensure_ascii=False)
    lines: list[str] = []
    for raw_line in serialized.splitlines():
        lines.extend(wrap(raw_line, width=96, replace_whitespace=False) or [""])
    return lines


def _content_stream(lines: Iterable[str], page_number: int, page_count: int) -> bytes:
    commands = ["BT", "/F1 9 Tf", "42 760 Td", "11 TL"]
    for line in lines:
        commands.append(f"({_escape_pdf_text(line)}) Tj T*")
    commands.extend(
        [
            f"0 -715 Td ({_escape_pdf_text(f'Page {page_number} of {page_count}')}) Tj",
            "ET",
        ]
    )
    return "\n".join(commands).encode("latin-1", "replace")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_document(objects: list[bytes]) -> bytes:
    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{object_number} 0 obj\n".encode())
        result.extend(body)
        result.extend(b"\nendobj\n")
    xref_offset = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(result)


__all__ = ["render_assessment_pdf"]
