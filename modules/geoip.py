import logging
import requests
import socket

log = logging.getLogger(__name__)


def run(domain):
    result = {"module": "geoip", "domain": domain, "status": "ok", "data": {}}

    try:
        ip = socket.gethostbyname(domain)
        result["data"]["ip"] = ip

        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8)
        resp.raise_for_status()
        geo = resp.json()

        result["data"].update({
            "ip":           geo.get("ip"),
            "city":         geo.get("city"),
            "region":       geo.get("region"),
            "country":      geo.get("country_name"),
            "country_code": geo.get("country_code"),
            "latitude":     geo.get("latitude"),
            "longitude":    geo.get("longitude"),
            "org":          geo.get("org"),
            "asn":          geo.get("asn"),
            "timezone":     geo.get("timezone"),
        })

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"geoip failed for {domain}: {e}")

    return result
