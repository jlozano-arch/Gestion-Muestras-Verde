# Countries and flags for coffee samples
COUNTRIES = {
    "CO": {"name": "Colombia", "flag": "🇨🇴"},
    "PE": {"name": "Perú", "flag": "🇵🇪"},
    "EC": {"name": "Ecuador", "flag": "🇪🇨"},
    "BO": {"name": "Bolivia", "flag": "🇧🇴"},
    "BR": {"name": "Brasil", "flag": "🇧🇷"},
    "ETH": {"name": "Etiopía", "flag": "🇪🇹"},
    "KE": {"name": "Kenia", "flag": "🇰🇪"},
    "UG": {"name": "Uganda", "flag": "🇺🇬"},
    "ZA": {"name": "Sudáfrica", "flag": "🇿🇦"},
    "MY": {"name": "Malasia", "flag": "🇲🇾"},
    "ID": {"name": "Indonesia", "flag": "🇮🇩"},
    "VN": {"name": "Vietnam", "flag": "🇻🇳"},
    "IN": {"name": "India", "flag": "🇮🇳"},
    "HN": {"name": "Honduras", "flag": "🇭🇳"},
    "GT": {"name": "Guatemala", "flag": "🇬🇹"},
    "SV": {"name": "El Salvador", "flag": "🇸🇻"},
    "CR": {"name": "Costa Rica", "flag": "🇨🇷"},
    "PA": {"name": "Panamá", "flag": "🇵🇦"},
    "MX": {"name": "México", "flag": "🇲🇽"},
}


def get_country_name(code: str) -> str:
    """Get country name by code"""
    return COUNTRIES.get(code, {}).get("name", code)


def get_country_flag(code: str) -> str:
    """Get country flag by code"""
    return COUNTRIES.get(code, {}).get("flag", "🌍")


def get_all_countries() -> dict:
    """Get all countries"""
    return COUNTRIES
