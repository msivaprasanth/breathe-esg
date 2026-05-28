import hashlib
import json
from dateutil import parser as dateparser
from datetime import date

UNIT_CONVERSIONS = {
    # Volume → Liters
    'l': 1.0, 'liter': 1.0, 'liters': 1.0, 'litre': 1.0, 'litres': 1.0,
    'gal': 3.78541, 'gallon': 3.78541, 'gallons': 3.78541,
    'ml': 0.001,
    'm3': 1000.0, 'm³': 1000.0,
    # Mass → KG
    'kg': 1.0, 'kilogram': 1.0, 'kilograms': 1.0,
    'g': 0.001, 'gram': 0.001,
    't': 1000.0, 'mt': 1000.0, 'tonne': 1000.0, 'ton': 907.185,
    'lb': 0.453592, 'lbs': 0.453592,
    # Energy → kWh
    'kwh': 1.0, 'kw/h': 1.0,
    'mwh': 1000.0,
    'gwh': 1000000.0,
    'mj': 0.277778,
    'gj': 277.778,
    # Distance → KM
    'km': 1.0, 'kilometer': 1.0, 'kilometers': 1.0, 'kilometre': 1.0,
    'mi': 1.60934, 'mile': 1.60934, 'miles': 1.60934,
    'nm': 1.852,  # nautical miles
}

def normalize_unit(value: float, raw_unit: str, target_type: str) -> tuple[float, str]:
    """
    Convert value from raw_unit to canonical unit.
    target_type: 'volume' → L, 'mass' → kg, 'energy' → kWh, 'distance' → km
    Returns (normalized_value, canonical_unit_str)
    """
    key = raw_unit.lower().strip()
    factor = UNIT_CONVERSIONS.get(key)
    if factor is None:
        return value, raw_unit  # unknown unit, pass through
    
    canonical_units = {
        'volume': 'L',
        'mass': 'kg',
        'energy': 'kWh',
        'distance': 'km',
    }
    return round(value * factor, 4), canonical_units.get(target_type, raw_unit)


def parse_date_flexible(date_str: str) -> date:
    """Handle DD.MM.YYYY, MM/DD/YYYY, YYYY-MM-DD, and variants."""
    if not date_str or str(date_str).strip() in ('', 'nan', 'NaT', 'None'):
        raise ValueError(f"Empty date string")
    date_str = str(date_str).strip()
    # Handle DD.MM.YYYY (SAP German format)
    if '.' in date_str and len(date_str) == 10:
        parts = date_str.split('.')
        if len(parts) == 3 and len(parts[2]) == 4:
            date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
    return dateparser.parse(date_str).date()


def make_row_hash(*fields) -> str:
    """Deterministic hash for deduplication."""
    content = json.dumps(fields, default=str, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def safe_float(val, default=0.0) -> float:
    try:
        s = str(val).replace(',', '').strip()
        if s in ('', 'nan', 'NaN', 'None', 'NaT', 'none'):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


# Airport IATA → coordinates for great-circle distance
AIRPORT_COORDS = {
    'BLR': (12.9499, 77.6681), 'DEL': (28.5562, 77.1000), 'BOM': (19.0896, 72.8656),
    'MAA': (12.9941, 80.1709), 'CCU': (22.6547, 88.4467), 'HYD': (17.2313, 78.4298),
    'AMD': (23.0772, 72.6347), 'PNQ': (18.5822, 73.9197), 'GOI': (15.3800, 73.8314),
    'JFK': (40.6413, -73.7781), 'LAX': (33.9425, -118.4081), 'ORD': (41.9742, -87.9073),
    'LHR': (51.4700, -0.4543), 'CDG': (49.0097, 2.5479), 'FRA': (50.0379, 8.5622),
    'DXB': (25.2532, 55.3657), 'SIN': (1.3644, 103.9915), 'NRT': (35.7720, 140.3929),
    'SYD': (-33.9399, 151.1753), 'GRU': (-23.4356, -46.4731), 'JNB': (-26.1367, 28.2411),
}

def great_circle_km(iata1: str, iata2: str) -> float | None:
    """Approximate great-circle distance in km between two IATA airports."""
    import math
    c1 = AIRPORT_COORDS.get(iata1.upper())
    c2 = AIRPORT_COORDS.get(iata2.upper())
    if not c1 or not c2:
        return None
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return round(6371 * 2 * math.asin(math.sqrt(a)), 1)