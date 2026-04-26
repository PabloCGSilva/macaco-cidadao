import io
from PIL import Image
import exifread


def extrair_gps(arquivo_bytes: bytes) -> tuple[float, float] | None:
    """Returns (latitude, longitude) from image EXIF or None."""
    try:
        tags = exifread.process_file(io.BytesIO(arquivo_bytes), details=False)
        if "GPS GPSLatitude" not in tags or "GPS GPSLongitude" not in tags:
            return None

        lat = _dms_to_decimal(tags["GPS GPSLatitude"].values, str(tags.get("GPS GPSLatitudeRef", "N")))
        lon = _dms_to_decimal(tags["GPS GPSLongitude"].values, str(tags.get("GPS GPSLongitudeRef", "E")))
        return lat, lon
    except Exception:
        return None


def _dms_to_decimal(dms, ref: str) -> float:
    d = float(dms[0].num) / float(dms[0].den)
    m = float(dms[1].num) / float(dms[1].den)
    s = float(dms[2].num) / float(dms[2].den)
    decimal = d + m / 60 + s / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal
