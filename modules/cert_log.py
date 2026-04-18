import logging
import requests

log = logging.getLogger(__name__)

CRT_SH_URL = "https://crt.sh/?q={}&output=json"


def run(domain):
    result = {"module": "certlog", "domain": domain, "status": "ok", "data": {}}

    try:
        resp = requests.get(CRT_SH_URL.format(f"%.{domain}"), timeout=15)
        resp.raise_for_status()
        entries = resp.json()

        seen = set()
        certs = []
        subdomains = set()

        for entry in entries:
            for line in entry.get("name_value", "").splitlines():
                line = line.strip().lstrip("*.")
                if line and line.endswith(domain):
                    subdomains.add(line)

            cert_id = entry.get("id")
            if cert_id not in seen:
                seen.add(cert_id)
                certs.append({
                    "id":          cert_id,
                    "common_name": entry.get("common_name", ""),
                    "issuer":      entry.get("issuer_name", ""),
                    "not_before":  entry.get("not_before", ""),
                    "not_after":   entry.get("not_after", ""),
                })

        result["data"]["subdomains"]    = sorted(subdomains)
        result["data"]["subdomain_count"] = len(subdomains)
        result["data"]["certificates"]  = certs[:50]
        result["data"]["cert_count"]    = len(seen)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"certlog failed for {domain}: {e}")

    return result
