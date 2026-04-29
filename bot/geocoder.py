"""
Reverse geocoding via Nominatim (OSM) — free, no API key required.
Rate limit: 1 request/second (enforced by caller).
"""
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"


def endereco_por_coords(lat: float, lon: float) -> str | None:
    """Returns a human-readable address string or None on failure."""
    params = urllib.parse.urlencode({
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,
    })
    url = f"{NOMINATIM}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "macaco-cidadao/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())

        addr = data.get("address", {})
        partes = []
        for campo in ("road", "house_number", "suburb", "neighbourhood", "city_district"):
            val = addr.get(campo, "").strip()
            if val:
                partes.append(val)

        return ", ".join(partes) if partes else data.get("display_name", "").split(",")[0]
    except Exception as e:
        logger.warning("Reverse geocoding falhou (%s, %s): %s", lat, lon, e)
        return None
