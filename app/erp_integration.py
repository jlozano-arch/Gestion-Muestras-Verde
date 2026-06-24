import csv
import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from openpyxl import load_workbook


ERP_DATA_PATH_ENV = "ERP_DATA_PATH"
ERP_SOURCE_ENV = "ERP_SOURCE"
ERP_APPS_SCRIPT_URL_ENV = "ERP_APPS_SCRIPT_URL"
ERP_SOURCE_FILE = "file"
ERP_SOURCE_APPS_SCRIPT = "apps_script"
ERP_LOG = logging.getLogger("app.erp_integration")

FIELD_ALIASES = {
    "cvc": {"cvc", "ctr compra", "ctr. compra", "contrato compra", "contrato de compra", "purchase contract"},
    "provider": {"proveedor", "supplier", "provider"},
    "supplier_reference": {"ref proveedor", "ref. proveedor", "referencia proveedor", "supplier reference", "supplier ref"},
    "quality": {"calidad", "quality", "description", "descripcion"},
    "origin": {"pais", "country", "origen", "origin", "pais origen"},
    "warehouse": {"almacen", "warehouse"},
    "warehouse_lot": {"almacen long no lote", "almacen long numero lote", "almacen lote", "no lote", "numero lote"},
    "sample_reference": {"muestra", "sample"},
    "bags_purchased": {"cantidad sacos", "sacos comprados", "bags purchased", "purchased bags", "sacos contrato"},
    "kg_purchased": {"kg teorico", "kg comprados", "kilos comprados", "purchased kg", "kg purchased", "contract kg"},
    "bags_available": {"stock sacos", "sacos disponibles", "available bags", "bags available"},
    "kg_available": {"kg disponibles", "kilos disponibles", "available kg", "kg available"},
    "purchase_price": {"precio fijo", "precio compra", "purchase price", "price", "precio"},
    "contract_date": {"fecha contrato", "contract date", "fecha compra", "purchase date"},
    "contract_status": {"estado", "estado contrato", "contract status", "status"},
    "incoterm": {"incoterm"},
    "comments": {"comentarios", "comments", "observaciones", "notes"},
}

RAW_APPS_SCRIPT_FIELD_MAP = {
    "cvc": "cvc",
    "proveedor": "provider",
    "ref_proveedor": "supplier_reference",
    "calidad": "quality",
    "pais_origen": "origin",
    "almacen": "warehouse",
    "almacen_lote": "warehouse_lot",
    "muestra": "sample_reference",
    "sacos_comprados": "bags_purchased",
    "kg_comprados": "kg_purchased",
    "sacos_disponibles": "bags_available",
    "kg_disponibles": "kg_available",
    "stock_sacos": "stock_bags",
    "precio_compra": "purchase_price",
    "fecha_contrato": "contract_date",
    "estado_contrato": "contract_status",
    "estado": "contract_status",
    "incoterm": "incoterm",
    "comentarios": "comments",
}

DISPLAY_LABELS = {
    "cvc": "CVC",
    "provider": "Proveedor ERP",
    "supplier_reference": "Ref. proveedor ERP",
    "quality": "Calidad ERP",
    "origin": "Pais/origen ERP",
    "warehouse": "Almacen ERP",
    "warehouse_lot": "Almacen / lote ERP",
    "sample_reference": "Muestra ERP",
    "bags_purchased": "Sacos comprados",
    "kg_purchased": "Kg comprados",
    "bags_available": "Sacos disponibles",
    "stock_bags": "Stock sacos",
    "kg_available": "Kg disponibles",
    "purchase_price": "Precio compra",
    "contract_date": "Fecha contrato",
    "contract_status": "Estado contrato",
    "incoterm": "Incoterm",
    "comments": "Comentarios ERP",
}


def normalize_cvc(cvc: str | None) -> str:
    if cvc is None:
        return ""
    text = str(cvc).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return "" if text in {"", "-", "N/A", "NA", "NONE", "NULL", "NAN"} else text


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"[._:/\\()\[\]-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


NORMALIZED_ALIASES = {
    field: {_normalize_text(alias) for alias in aliases}
    for field, aliases in FIELD_ALIASES.items()
}

APPS_SCRIPT_FIELD_MAP = {
    _normalize_text(raw_key): field
    for raw_key, field in RAW_APPS_SCRIPT_FIELD_MAP.items()
}


def _field_for_header(header: Any) -> str | None:
    normalized = _normalize_text(header)
    if not normalized:
        return None
    for field, aliases in NORMALIZED_ALIASES.items():
        if normalized in aliases:
            return field
    return None


def _clean_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return "" if text.lower() in {"", "-", "none", "null", "nan", "n/a", "na"} else text


def _mapped_record(headers: list[Any], values: list[Any], source_sheet: str | None = None) -> dict[str, str]:
    record: dict[str, str] = {}
    for index, header in enumerate(headers):
        field = _field_for_header(header)
        if not field or field in record:
            continue
        value = values[index] if index < len(values) else None
        cleaned = _clean_value(value)
        if cleaned:
            record[field] = normalize_cvc(cleaned) if field == "cvc" else cleaned
    if source_sheet:
        record["source_sheet"] = source_sheet
    return record


def _read_csv(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        reader = csv.reader(handle, dialect)
        all_rows = list(reader)
    if not all_rows:
        return rows
    headers = all_rows[0]
    for values in all_rows[1:]:
        record = _mapped_record(headers, values)
        if record:
            rows.append(record)
    return rows


def _find_header_row(sheet) -> tuple[int, list[Any]] | None:
    for row_index, row in enumerate(sheet.iter_rows(min_row=1, max_row=15, values_only=True), start=1):
        mapped_fields = {_field_for_header(value) for value in row}
        mapped_fields.discard(None)
        if "cvc" in mapped_fields and len(mapped_fields) >= 2:
            return row_index, list(row)
    return None


def _read_excel(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    workbook = load_workbook(path, read_only=True, data_only=True)
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        header = _find_header_row(sheet)
        if not header:
            continue
        header_row_index, headers = header
        for values in sheet.iter_rows(min_row=header_row_index + 1, values_only=True):
            record = _mapped_record(headers, list(values), source_sheet=sheet_name)
            if record:
                rows.append(record)
    workbook.close()
    return rows


def _read_erp_records(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt", ".tsv"}:
        return _read_csv(path)
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return _read_excel(path)
    return []


def _status(status: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, **extra}


def _normalize_apps_script_record(record: dict[str, Any] | None) -> dict[str, str]:
    normalized = {}
    for raw_key, raw_value in (record or {}).items():
        key = APPS_SCRIPT_FIELD_MAP.get(_normalize_text(raw_key))
        if not key:
            continue
        value = _clean_value(raw_value)
        if value:
            normalized[key] = normalize_cvc(value) if key == "cvc" else value
    return normalized


def _log_apps_script_response(url: str, response: httpx.Response, payload: Any = None) -> None:
    ERP_LOG.warning("ERP Apps Script URL consultada: %s", url)
    ERP_LOG.warning("ERP Apps Script status_code: %s", response.status_code)
    ERP_LOG.warning("ERP Apps Script content-type: %s", response.headers.get("content-type", ""))
    ERP_LOG.warning("ERP Apps Script response.text[0:500]: %s", response.text[:500])
    ERP_LOG.warning("ERP Apps Script response.json(): %s", payload)


def _apps_script_lookup(cvc: str) -> dict | None:
    normalized_cvc = normalize_cvc(cvc)
    endpoint = os.getenv(ERP_APPS_SCRIPT_URL_ENV, "").strip()
    if not endpoint:
        return _status("not_configured", message=f"{ERP_APPS_SCRIPT_URL_ENV} no configurado")
    if not normalized_cvc:
        return _status("no_cvc")

    separator = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{separator}{urlencode({'action': 'getDatosMuestraERP', 'cvc': normalized_cvc})}"
    try:
        with httpx.Client(follow_redirects=True, timeout=8.0, headers={"Accept": "application/json"}) as client:
            response = client.get(url)
        try:
            payload = response.json()
        except Exception:
            payload = json.loads(response.text)
        _log_apps_script_response(url, response, payload)
        response.raise_for_status()
    except Exception as exc:
        return _status("error", message=f"No se pudo consultar Apps Script: {exc}", source="google_sheets_largos")

    status = _clean_value(payload.get("status")).lower()
    source = _clean_value(payload.get("source")) or "google_sheets_largos"
    if status == "not_found":
        return None
    if status == "found":
        return _status(
            "found",
            cvc=normalize_cvc(payload.get("cvc") or normalized_cvc),
            data=_normalize_apps_script_record(payload.get("data")),
            source=source,
            warnings=payload.get("warnings") or [],
        )
    if status == "multiple":
        matches = [_normalize_apps_script_record(item) for item in payload.get("matches") or []]
        return _status(
            "multiple",
            cvc=normalize_cvc(payload.get("cvc") or normalized_cvc),
            count=len(matches),
            matches=matches,
            source=source,
            warnings=payload.get("warnings") or [],
        )
    if status == "error":
        return _status(
            "error",
            message=_clean_value(payload.get("message")) or "Error devuelto por Apps Script",
            source=source,
            warnings=payload.get("warnings") or [],
        )
    return _status("error", message=f"Respuesta ERP no reconocida: {status or 'sin status'}", source=source)


def _file_lookup(cvc: str) -> dict | None:
    normalized_cvc = normalize_cvc(cvc)
    erp_path = os.getenv(ERP_DATA_PATH_ENV, "").strip()
    if not erp_path:
        return _status("not_configured")
    path = Path(erp_path)
    if not path.exists() or not path.is_file():
        return _status("not_configured", message=f"{ERP_DATA_PATH_ENV} no apunta a un archivo valido")
    if not normalized_cvc:
        return _status("no_cvc")

    try:
        records = _read_erp_records(path)
    except Exception as exc:
        return _status("not_configured", message=f"No se pudo leer {ERP_DATA_PATH_ENV}: {exc}")
    matches = [record for record in records if normalize_cvc(record.get("cvc")) == normalized_cvc]
    if not matches:
        return None
    if len(matches) > 1:
        return _status("multiple", cvc=normalized_cvc, count=len(matches), matches=matches, source=ERP_SOURCE_FILE)
    return _status("found", cvc=normalized_cvc, data=matches[0], source=ERP_SOURCE_FILE)


def get_erp_data_by_cvc(cvc: str) -> dict | None:
    """Read-only lookup of ERP data by exact normalized CVC."""
    source = os.getenv(ERP_SOURCE_ENV, ERP_SOURCE_FILE).strip().lower()
    if source == ERP_SOURCE_APPS_SCRIPT:
        return _apps_script_lookup(cvc)
    return _file_lookup(cvc)


def erp_display_rows(data: dict | None, public: bool = False) -> list[dict[str, str]]:
    if not data or data.get("status") != "found":
        return []
    record = data.get("data") or {}
    fields = [
        "quality",
        "supplier_reference",
        "warehouse_lot",
        "sample_reference",
        "bags_available",
        "stock_bags",
        "kg_available",
        "contract_status",
    ] if public else [
        "cvc",
        "provider",
        "supplier_reference",
        "quality",
        "warehouse_lot",
        "sample_reference",
        "bags_purchased",
        "kg_purchased",
        "bags_available",
        "stock_bags",
        "kg_available",
        "purchase_price",
        "incoterm",
        "contract_status",
        "comments",
    ]
    rows = []
    for field in fields:
        value = _clean_value(record.get(field))
        if value:
            rows.append({"label": DISPLAY_LABELS[field], "value": value})
    return rows
