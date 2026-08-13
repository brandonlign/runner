import math
OBLIQUITY_DEG = 23.43928

def wrap180(value):
    return (float(value) + 180.0) % 360.0 - 180.0

def to_ecliptic(ra_deg, dec_deg):
    ra = math.radians(float(ra_deg))
    dec = math.radians(float(dec_deg))
    eps = math.radians(OBLIQUITY_DEG)
    x = math.cos(dec) * math.cos(ra)
    y = math.cos(dec) * math.sin(ra) * math.cos(eps) + math.sin(dec) * math.sin(eps)
    z = -math.cos(dec) * math.sin(ra) * math.sin(eps) + math.sin(dec) * math.cos(eps)
    lon = math.degrees(math.atan2(y, x)) % 360.0
    lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    return lon, lat

def canonical(sol_deg, ra_deg, dec_deg, vg):
    lon, lat = to_ecliptic(ra_deg, dec_deg)
    return float(sol_deg), wrap180(lon - float(sol_deg)), lat, float(vg)

def circular_error(a, b):
    return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)
