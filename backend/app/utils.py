import re

def _normalize_name(s: str) -> str:
    return re.sub(r"[^A-Za-z]+", "", s or "").upper()

def build_house_id(zone: str, householder_fullname: str, serial_number: str) -> str:
    zone_ = (zone or "").strip().upper()
    parts = [p for p in (householder_fullname or "").strip().split() if p]
    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""
    fn = _normalize_name(first_name)
    ln = _normalize_name(last_name)
    fn1 = (fn[:1] or "X")
    ln3 = (ln[:3] or "XXX").ljust(3, "X")
    digits = re.sub(r"\D", "", serial_number or "")
    tail3 = digits[-3:].rjust(3, "0")
    return f"{zone_}{fn1}{ln3}{tail3}"
