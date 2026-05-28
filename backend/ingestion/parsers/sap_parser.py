import pandas as pd
import io
from datetime import date, timedelta
from .utils import parse_date_flexible, normalize_unit, make_row_hash, safe_float

# German → English column mapping
COLUMN_MAP = {
    'buchungsdatum': 'posting_date',
    'posting date': 'posting_date',
    'belegdatum': 'posting_date',
    'material': 'material',
    'materialbezeichnung': 'material_description',
    'material description': 'material_description',
    'kurztext': 'material_description',
    'werk': 'plant',
    'plant': 'plant',
    'bewegungsart': 'movement_type',
    'movement type': 'movement_type',
    'mvt': 'movement_type',
    'menge': 'quantity',
    'quantity': 'quantity',
    'amount': 'quantity',
    'bme': 'unit',
    'unit of entry': 'unit',
    'base unit': 'unit',
    'einheit': 'unit',
    'unit': 'unit',
    'betrag in hw': 'amount_lc',
    'amount in lc': 'amount_lc',
    'wert in hw': 'amount_lc',
    'kostenstelle': 'cost_center',
    'cost center': 'cost_center',
    'lieferant': 'vendor',
    'vendor': 'vendor',
    'bestellung': 'purchase_order',
    'purchase order': 'purchase_order',
    'po number': 'purchase_order',
}

# Material codes/descriptions that indicate fuel
FUEL_KEYWORDS = [
    'diesel', 'petrol', 'gasoline', 'benzin', 'kraftstoff', 'fuel',
    'kerosene', 'kerosin', 'lpg', 'lng', 'cng', 'gas oil', 'gasoil',
    'furnace oil', 'hfo', 'lubricant', 'lubrikat', 'oil', 'öl',
]

# Movement types: goods receipt (101), goods issue/consumption (201, 261, 262)
CONSUMPTION_MOVEMENT_TYPES = {'201', '261', '262', '551', '601'}
GR_MOVEMENT_TYPES = {'101', '501'}

# Unit type classification for normalization
VOLUME_UNITS = {'l', 'liter', 'liters', 'litre', 'litres', 'gal', 'gallon', 'gallons', 'ml', 'm3', 'kl'}
MASS_UNITS = {'kg', 'g', 't', 'mt', 'tonne', 'ton', 'lb', 'lbs', 'kilogram'}


def _is_fuel(material: str, description: str) -> bool:
    combined = f"{material} {description}".lower()
    return any(kw in combined for kw in FUEL_KEYWORDS)


def _classify_scope_category(material: str, description: str, movement_type: str):
    """Fuel consumption → Scope 1. Procurement → Scope 3."""
    if _is_fuel(material, description):
        mt = str(movement_type).strip()
        if mt in CONSUMPTION_MOVEMENT_TYPES or mt in GR_MOVEMENT_TYPES:
            return '1', 'MOBILE_COMBUSTION'
    return '3', 'PURCHASED_GOODS'


def _normalize_quantity(qty: float, unit: str):
    unit_lower = unit.lower().strip()
    if unit_lower in VOLUME_UNITS:
        return normalize_unit(qty, unit, 'volume')
    elif unit_lower in MASS_UNITS:
        return normalize_unit(qty, unit, 'mass')
    return qty, unit


def _flag_row(row: dict) -> list:
    flags = []
    if row.get('quantity', 0) <= 0:
        flags.append('Zero or negative quantity')
    if not row.get('plant'):
        flags.append('Missing plant code')
    if row.get('quantity', 0) > 500000:
        flags.append('Unusually large quantity — verify')
    if not row.get('posting_date'):
        flags.append('Missing posting date')
    return flags


def parse(file_content: bytes, filename: str, tenant_plant_lookup: dict = None) -> list[dict]:
    """
    Parse SAP CSV/XLSX export.
    Returns list of dicts, each representing one normalized EmissionRecord payload.
    """
    tenant_plant_lookup = tenant_plant_lookup or {}
    
    try:
        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        else:
            # Try different encodings (SAP sometimes exports in latin-1)
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    df = pd.read_csv(io.BytesIO(file_content), dtype=str, encoding=enc, sep=None, engine='python')
                    break
                except Exception:
                    continue
    except Exception as e:
        raise ValueError(f"Could not parse file: {e}")

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    rename = {col: COLUMN_MAP[col] for col in df.columns if col in COLUMN_MAP}
    df = df.rename(columns=rename)

    required = {'posting_date', 'quantity', 'unit'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns after mapping: {missing}. Found: {list(df.columns)}")

    records = []
    parse_errors = []

    for idx, row in df.iterrows():
        try:
            raw_qty = safe_float(row.get('quantity', 0))
            raw_unit = str(row.get('unit', '')).strip()
            material = str(row.get('material', '')).strip()
            description = str(row.get('material_description', '')).strip()
            plant_code = str(row.get('plant', '')).strip()
            movement_type = str(row.get('movement_type', '')).strip()
            posting_date_str = str(row.get('posting_date', '')).strip()

            posting_date = parse_date_flexible(posting_date_str)
            norm_qty, norm_unit = _normalize_quantity(raw_qty, raw_unit)
            scope, category = _classify_scope_category(material, description, movement_type)

            plant_name = tenant_plant_lookup.get(plant_code, plant_code)

            record = {
                'scope': scope,
                'category': category,
                'period_start': posting_date,
                'period_end': posting_date,
                'quantity': norm_qty,
                'quantity_unit': norm_unit,
                'raw_quantity': raw_qty,
                'raw_unit': raw_unit,
                'source_metadata': {
                    'plant_code': plant_code,
                    'plant_name': plant_name,
                    'material': material,
                    'material_description': description,
                    'movement_type': movement_type,
                    'vendor': str(row.get('vendor', '')).strip(),
                    'cost_center': str(row.get('cost_center', '')).strip(),
                    'purchase_order': str(row.get('purchase_order', '')).strip(),
                    'amount_lc': safe_float(row.get('amount_lc', 0)),
                    'source_row': idx + 2,
                },
                'flag_reasons': _flag_row({
                    'quantity': norm_qty,
                    'plant': plant_code,
                    'posting_date': posting_date,
                }),
                'source_row_hash': make_row_hash(
                    posting_date_str, material, plant_code, raw_qty, raw_unit, movement_type
                ),
            }
            records.append(record)
        except Exception as e:
            parse_errors.append({'row': idx + 2, 'error': str(e)})

    return records, parse_errors
