import pandas as pd
import io
from datetime import date, timedelta
from .utils import parse_date_flexible, normalize_unit, make_row_hash, safe_float

COLUMN_MAP = {

    # ─────────────────────────────────────
    # Meter identification
    # ─────────────────────────────────────
    'meter id': 'meter_id',
    'meterid': 'meter_id',
    'meter id number': 'meter_id',
    'account number': 'meter_id',
    'account no': 'meter_id',
    'consumer number': 'meter_id',
    'consumer id': 'meter_id',
    'meter': 'meter_id',

    # ─────────────────────────────────────
    # Billing period start
    # ─────────────────────────────────────
    'billing period start': 'period_start',
    'period start': 'period_start',
    'start date': 'period_start',
    'from date': 'period_start',
    'bill from': 'period_start',
    'service start': 'period_start',
    'reading date from': 'period_start',

    # ─────────────────────────────────────
    # Billing period end
    # ─────────────────────────────────────
    'billing period end': 'period_end',
    'period end': 'period_end',
    'end date': 'period_end',
    'to date': 'period_end',
    'bill to': 'period_end',
    'service end': 'period_end',
    'reading date to': 'period_end',

    # ─────────────────────────────────────
    # Consumption / Energy
    # ─────────────────────────────────────
    'consumption': 'consumption',
    'consumption kwh': 'consumption',
    'usage': 'consumption',
    'usage kwh': 'consumption',
    'electricity kwh': 'consumption',
    'kwh used': 'consumption',
    'kwh': 'consumption',
    'energy': 'consumption',
    'energy consumed': 'consumption',
    'electricity consumed': 'consumption',
    'units consumed': 'consumption',
    'net consumption': 'consumption',
    'total kwh': 'consumption',

    # ─────────────────────────────────────
    # Unit of measure
    # ─────────────────────────────────────
    'unit': 'unit',
    'uom': 'unit',
    'unit of measure': 'unit',
    'units': 'unit',

    # ─────────────────────────────────────
    # Site / Facility / Location
    # ─────────────────────────────────────
    'site': 'site',
    'site name': 'site',
    'facility': 'site',
    'facility name': 'site',
    'location': 'site',
    'premise': 'site',
    'address': 'site',
    'plant': 'site',

    # ─────────────────────────────────────
    # Tariff / Rate
    # ─────────────────────────────────────
    'tariff': 'tariff',
    'tariff code': 'tariff',
    'tariff type': 'tariff',
    'rate plan': 'tariff',
    'rate code': 'tariff',
    'rate type': 'tariff',

    # ─────────────────────────────────────
    # Financial fields
    # ─────────────────────────────────────
    'amount': 'amount',
    'bill amount': 'amount',
    'invoice amount': 'amount',
    'total amount': 'amount',
    'total charges': 'amount',
    'charges': 'amount',
    'cost': 'amount',

    # ─────────────────────────────────────
    # Currency
    # ─────────────────────────────────────
    'currency': 'currency',
    'currency code': 'currency',

    # ─────────────────────────────────────
    # Utility provider
    # ─────────────────────────────────────
    'provider': 'provider',
    'utility provider': 'provider',
    'supplier': 'provider',
    'vendor': 'provider',

    # ─────────────────────────────────────
    # Country / Geography
    # ─────────────────────────────────────
    'country': 'country',
    'region': 'region',
}


def _prorate_to_month(period_start: date, period_end: date, consumption: float) -> list[dict]:
    """
    If billing period spans multiple calendar months, prorate consumption
    proportionally to each month. Returns list of {period_start, period_end, quantity}.
    """
    if period_start.year == period_end.year and period_start.month == period_end.month:
        return [{'period_start': period_start, 'period_end': period_end, 'quantity': consumption}]

    total_days = (period_end - period_start).days
    if total_days <= 0:
        return [{'period_start': period_start, 'period_end': period_end, 'quantity': consumption}]

    results = []
    current = period_start
    while current <= period_end:
        # End of current month
        if current.month == 12:
            month_end = date(current.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
        
        slice_end = min(month_end, period_end)
        slice_days = (slice_end - current).days + 1
        prorated = round(consumption * slice_days / total_days, 4)
        results.append({'period_start': current, 'period_end': slice_end, 'quantity': prorated})
        current = slice_end + timedelta(days=1)

    return results


def _flag_row(consumption: float, period_start: date, period_end: date, meter_id: str) -> list:
    flags = []
    if consumption <= 0:
        flags.append('Zero or negative consumption')
    if not meter_id:
        flags.append('Missing meter ID')
    days = (period_end - period_start).days
    if days < 0:
        flags.append('End date before start date')
    if days > 95:
        flags.append('Billing period unusually long (>3 months)')
    if consumption > 1_000_000:
        flags.append('Consumption > 1 GWh — verify unit (kWh vs MWh?)')
    return flags


def parse(file_content: bytes, filename: str, tenant_plant_lookup: dict = None) -> tuple[list, list]:
    try:
        if filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        else:
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    df = pd.read_csv(io.BytesIO(file_content), dtype=str, encoding=enc, sep=None, engine='python')
                    break
                except Exception:
                    continue
    except Exception as e:
        raise ValueError(f"Could not parse file: {e}")

    df.columns = [c.strip().lower().replace('_'," ") for c in df.columns]
    rename = {col: COLUMN_MAP[col] for col in df.columns if col in COLUMN_MAP}
    df = df.rename(columns=rename)

    if 'consumption' not in df.columns:
        raise ValueError(f"Could not find consumption column. Found: {list(df.columns)}")
    if 'period_start' not in df.columns or 'period_end' not in df.columns:
        raise ValueError(f"Could not find billing period columns. Found: {list(df.columns)}")

    records = []
    parse_errors = []

    for idx, row in df.iterrows():
        try:
            raw_qty = safe_float(row.get('consumption', 0))
            raw_unit = str(row.get('unit', 'kWh')).strip() or 'kWh'
            norm_qty, norm_unit = normalize_unit(raw_qty, raw_unit, 'energy')

            period_start = parse_date_flexible(str(row.get('period_start', '')))
            period_end = parse_date_flexible(str(row.get('period_end', '')))
            meter_id = str(row.get('meter_id', '')).strip()
            site = str(row.get('site', '')).strip()
            tariff = str(row.get('tariff', '')).strip()

            # Prorate across calendar months if needed
            slices = _prorate_to_month(period_start, period_end, norm_qty)

            for sl in slices:
                flags = _flag_row(sl['quantity'], sl['period_start'], sl['period_end'], meter_id)
                record = {
                    'scope': '2',
                    'category': 'PURCHASED_ELECTRICITY',
                    'period_start': sl['period_start'],
                    'period_end': sl['period_end'],
                    'quantity': sl['quantity'],
                    'quantity_unit': norm_unit,
                    'raw_quantity': raw_qty,
                    'raw_unit': raw_unit,
                    'source_metadata': {
                        'meter_id': meter_id,
                        'site': site,
                        'tariff': tariff,
                        'amount': safe_float(row.get('amount', 0)),
                        'original_period_start': str(period_start),
                        'original_period_end': str(period_end),
                        'prorated': len(slices) > 1,
                        'source_row': idx + 2,
                    },
                    'flag_reasons': flags,
                    'source_row_hash': make_row_hash(
                        str(period_start), str(period_end), meter_id, raw_qty, raw_unit
                    ),
                }
                records.append(record)
        except Exception as e:
            parse_errors.append({'row': idx + 2, 'error': str(e)})

    return records, parse_errors