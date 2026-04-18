import logging
import requests
import socket

log = logging.getLogger(__name__)

SHODAN_URL = "https://api.shodan.io/shodan/host/{}"


def run(domain, api_key=None):
    result = {"module": "shodan", "domain": domain, "status": "ok", "data": {}}

    if not api_key:
        result["status"] = "skipped"
        result["reason"] = "no api key"
        return result

    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        result["status"] = "error"
        result["error"] = "could not resolve domain"
        return result

    result["data"]["ip"] = ip

    try:
        resp = requests.get(SHODAN_URL.format(ip), params={"key": api_key}, timeout=10)

        if resp.status_code == 404:
            result["data"]["note"] = "host not indexed in shodan"
            return result

        resp.raise_for_status()
        host = resp.json()

        ports    = []
        services = []
        for item in host.get("data", []):
            port = item.get("port")
            if port:
                ports.append(port)
                services.append({
                    "port":      port,
                    "transport": item.get("transport", "tcp"),
                    "product":   item.get("product", ""),
                    "version":   item.get("version", ""),
                    "banner":    item.get("data", "")[:200].strip(),
                })

        result["data"].update({
            "org":         host.get("org"),
            "isp":         host.get("isp"),
            "country":     host.get("country_name"),
            "city":        host.get("city"),
            "os":          host.get("os"),
            "hostnames":   host.get("hostnames", []),
            "open_ports":  sorted(set(ports)),
            "services":    services,
            "vulns":       list(host.get("vulns", {}).keys()),
            "tags":        host.get("tags", []),
            "last_update": host.get("last_update"),
        })

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"shodan failed for {domain}: {e}")

    return result
