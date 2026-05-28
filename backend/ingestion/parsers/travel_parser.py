import pandas as pd
import io
import math

from .utils import (
    parse_date_flexible,
    make_row_hash,
    safe_float,
    great_circle_km,
)

COLUMN_MAP = {

    # ─────────────────────────────────────
    # Employee fields
    # ─────────────────────────────────────
    'employee id': 'employee_id',
    'emp id': 'employee_id',
    'staff id': 'employee_id',
    'traveler id': 'employee_id',
    'employee number': 'employee_id',

    # ─────────────────────────────────────
    # Travel date
    # ─────────────────────────────────────
    'trip date': 'trip_date',
    'travel date': 'trip_date',
    'departure date': 'trip_date',
    'check in date': 'trip_date',
    'transaction date': 'trip_date',
    'expense date': 'trip_date',
    'date': 'trip_date',

    # ─────────────────────────────────────
    # Category / transport mode
    # ─────────────────────────────────────
    'category': 'category',
    'expense type': 'category',
    'travel type': 'category',
    'transport type': 'category',
    'transport mode': 'category',
    'mode of transport': 'category',
    'mode': 'category',

    # ─────────────────────────────────────
    # Origin
    # ─────────────────────────────────────
    'origin': 'origin',
    'from': 'origin',
    'departure': 'origin',
    'from airport': 'origin',
    'origin airport': 'origin',
    'departure airport': 'origin',

    # ─────────────────────────────────────
    # Destination
    # ─────────────────────────────────────
    'destination': 'destination',
    'to': 'destination',
    'arrival': 'destination',
    'to airport': 'destination',
    'destination airport': 'destination',
    'arrival airport': 'destination',

    # ─────────────────────────────────────
    # Travel class
    # ─────────────────────────────────────
    'class': 'travel_class',
    'travel class': 'travel_class',
    'cabin class': 'travel_class',
    'fare class': 'travel_class',
    'service class': 'travel_class',

    # ─────────────────────────────────────
    # Nights
    # ─────────────────────────────────────
    'nights': 'nights',
    'hotel nights': 'nights',
    'number of nights': 'nights',
    'stay nights': 'nights',

    # ─────────────────────────────────────
    # Distance
    # ─────────────────────────────────────
    'distance': 'distance_km',
    'distance km': 'distance_km',
    'km': 'distance_km',
    'kilometers': 'distance_km',
    'miles': 'distance_miles',

    # ─────────────────────────────────────
    # Amount
    # ─────────────────────────────────────
    'amount': 'amount',
    'cost': 'amount',
    'fare': 'amount',
    'expense amount': 'amount',
    'total cost': 'amount',
    'charges': 'amount',

    # ─────────────────────────────────────
    # Currency
    # ─────────────────────────────────────
    'currency': 'currency',
    'currency code': 'currency',

    # ─────────────────────────────────────
    # Vendor
    # ─────────────────────────────────────
    'vendor': 'vendor',
    'airline': 'vendor',
    'carrier': 'vendor',
    'hotel': 'vendor',
    'hotel name': 'vendor',
    'provider': 'vendor',
}


# Emission factors (future use)
FLIGHT_EMISSION_FACTORS = {
    'economy': 0.255,
    'premium economy': 0.387,
    'business': 0.765,
    'first': 1.020,
}

HOTEL_EMISSION_FACTOR = 31.0
CAR_RENTAL_FACTOR = 0.21
TAXI_FACTOR = 0.21
RAIL_FACTOR = 0.041


CATEGORY_MAP = {
    # AIR
    'air': 'AIR',
    'flight': 'AIR',
    'airline': 'AIR',
    'fly': 'AIR',
    'domestic flight': 'AIR',
    'international flight': 'AIR',

    # HOTEL
    'hotel': 'HTL',
    'htl': 'HTL',
    'accommodation': 'HTL',
    'lodging': 'HTL',

    # CAR
    'car': 'CAR',
    'car rental': 'CAR',
    'rental car': 'CAR',
    'auto': 'CAR',

    # TAXI
    'taxi': 'TAXI',
    'cab': 'TAXI',
    'rideshare': 'TAXI',
    'uber': 'TAXI',
    'ola': 'TAXI',

    # RAIL
    'rail': 'RAIL',
    'train': 'RAIL',
    'railway': 'RAIL',

    # GROUND fallback
    'ground': 'CAR',
    'bus': 'CAR',
}


SCOPE3_CATEGORY_MAP = {
    'AIR': 'BUSINESS_TRAVEL_AIR',
    'HTL': 'BUSINESS_TRAVEL_HOTEL',
    'CAR': 'BUSINESS_TRAVEL_GROUND',
    'TAXI': 'BUSINESS_TRAVEL_GROUND',
    'RAIL': 'BUSINESS_TRAVEL_GROUND',
}


def clean_nan(value):
    """
    Convert pandas NaN values to None.
    """
    if pd.isna(value):
        return None
    return value


def _normalize_category(raw: str) -> str:
    if not raw:
        return 'CAR'

    return CATEGORY_MAP.get(
        raw.lower().strip(),
        'CAR'
    )


def _normalize_class(raw: str) -> str:
    if not raw:
        return 'economy'

    r = raw.lower().strip()

    if 'first' in r:
        return 'first'

    if 'business' in r or 'biz' in r:
        return 'business'

    if 'premium' in r:
        return 'premium economy'

    return 'economy'


def _safe_nan_float(value, default=0):
    """
    Safe float conversion that handles NaN properly.
    """
    val = safe_float(value, default)

    try:
        if math.isnan(val):
            return default
    except Exception:
        pass

    return val


def _compute_quantity_and_unit(cat: str, row: dict):
    """
    Returns:
        (quantity, unit, flag_reasons)
    """

    flags = []

    # AIR TRAVEL
    if cat == 'AIR':

        origin = str(row.get('origin') or '').strip().upper()
        dest = str(row.get('destination') or '').strip().upper()

        dist = _safe_nan_float(
            row.get('distance_km'),
            default=0
        )

        # Attempt airport-based calculation
        if dist <= 0:

            dist_calc = great_circle_km(origin, dest)

            if dist_calc:
                dist = dist_calc
            else:
                dist = 0
                flags.append(
                    f'Could not calculate distance for {origin} → {dest}'
                )

        if dist <= 0:
            flags.append(
                'Missing distance — emission calculation unreliable'
            )

        return dist, 'km', flags

    # HOTEL
    elif cat == 'HTL':

        nights = _safe_nan_float(
            row.get('nights'),
            default=1
        )

        if nights <= 0:
            nights = 1
            flags.append(
                'Hotel nights defaulted to 1'
            )

        return nights, 'nights', flags

    # GROUND TRANSPORT
    else:

        dist = _safe_nan_float(
            row.get('distance_km'),
            default=0
        )

        # Fallback miles conversion
        if dist <= 0:

            miles = _safe_nan_float(
                row.get('distance_miles'),
                default=0
            )

            dist = miles * 1.60934

        if dist <= 0:
            flags.append(
                'Missing distance for ground transport'
            )

        return dist, 'km', flags


def _flag_row(cat: str, qty: float, employee_id: str):

    flags = []

    if not employee_id:
        flags.append('Missing employee ID')

    if qty <= 0 and cat != 'HTL':
        flags.append('Zero quantity / distance')

    if cat == 'AIR' and qty > 20000:
        flags.append(
            'Flight distance > 20,000 km — verify route'
        )

    return flags


def parse(
    file_content: bytes,
    filename: str
) -> tuple[list, list]:

    try:

        # EXCEL
        if filename.lower().endswith(('.xlsx', '.xls')):

            df = pd.read_excel(
                io.BytesIO(file_content),
                dtype=str
            )

        # CSV
        else:

            df = None

            for enc in ('utf-8', 'latin-1', 'cp1252'):

                try:

                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        dtype=str,
                        encoding=enc,
                        sep=None,
                        engine='python'
                    )

                    break

                except Exception:
                    continue

            if df is None:
                raise ValueError(
                    'Could not decode CSV file'
                )

    except Exception as e:
        raise ValueError(f'Could not parse file: {e}')

    # Normalize column names
    df.columns = [
        c.strip().lower().replace('_', ' ')
        for c in df.columns
    ]

    # Rename mapped columns
    rename = {
        col: COLUMN_MAP[col]
        for col in df.columns
        if col in COLUMN_MAP
    }

    df = df.rename(columns=rename)

    # Required fields
    if 'trip_date' not in df.columns:
        raise ValueError(
            f'Could not find date column. Found: {list(df.columns)}'
        )

    if 'category' not in df.columns:
        raise ValueError(
            f'Could not find category column. Found: {list(df.columns)}'
        )

    records = []
    parse_errors = []

    for idx, row in df.iterrows():

        try:

            # Clean NaN values
            row = {
                k: clean_nan(v)
                for k, v in row.to_dict().items()
            }

            trip_date = parse_date_flexible(
                str(row.get('trip_date', ''))
            )

            raw_cat = str(
                row.get('category') or 'AIR'
            )

            cat = _normalize_category(raw_cat)

            travel_class = _normalize_class(
                str(row.get('travel_class') or 'Economy')
            )

            employee_id = str(
                row.get('employee_id') or ''
            ).strip()

            origin = str(
                row.get('origin') or ''
            ).strip().upper()

            dest = str(
                row.get('destination') or ''
            ).strip().upper()

            qty, unit, calc_flags = _compute_quantity_and_unit(
                cat,
                row
            )

            flags = (
                _flag_row(cat, qty, employee_id)
                + calc_flags
            )

            scope3_cat = SCOPE3_CATEGORY_MAP.get(
                cat,
                'BUSINESS_TRAVEL_GROUND'
            )

            record = {
                'scope': '3',

                'category': scope3_cat,

                'period_start': trip_date,
                'period_end': trip_date,

                'quantity': qty,
                'quantity_unit': unit,

                'raw_quantity': qty,
                'raw_unit': unit,

                'source_metadata': {
                    'employee_id': employee_id,
                    'transport_category': cat,
                    'travel_class': travel_class,
                    'origin': origin,
                    'destination': dest,

                    'vendor': str(
                        row.get('vendor') or ''
                    ).strip(),

                    'amount': _safe_nan_float(
                        row.get('amount'),
                        default=0
                    ),

                    'currency': str(
                        row.get('currency') or ''
                    ).strip(),

                    'nights': (
                        _safe_nan_float(
                            row.get('nights'),
                            default=0
                        )
                        if row.get('nights') is not None
                        else None
                    ),

                    'raw_category': raw_cat,

                    'source_row': idx + 2,
                },

                'flag_reasons': flags,

                'source_row_hash': make_row_hash(
                    str(trip_date),
                    employee_id,
                    cat,
                    origin,
                    dest,
                    qty
                ),
            }

            records.append(record)

        except Exception as e:

            parse_errors.append({
                'row': idx + 2,
                'error': str(e)
            })

    return records, parse_errors