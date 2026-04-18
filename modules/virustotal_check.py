import logging
import requests

log = logging.getLogger(__name__)

VT_URL = "https://www.virustotal.com/api/v3/domains/{}"


def run(domain, api_key=None):
    result = {"module": "virustotal", "domain": domain, "status": "ok", "data": {}}

    if not api_key:
        result["status"] = "skipped"
        result["reason"] = "no api key"
        return result

    try:
        resp = requests.get(VT_URL.format(domain), headers={"x-apikey": api_key}, timeout=10)
        resp.raise_for_status()
        attrs = resp.json().get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})

        result["data"] = {
            "reputation": attrs.get("reputation", 0),
            "malicious":  stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless":   stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "categories": attrs.get("categories", {}),
            "registrar":  attrs.get("registrar"),
            "tld":        attrs.get("tld"),
            "flag":       None,
        }

        if result["data"]["malicious"] > 0:
            result["data"]["flag"] = f"flagged malicious by {result['data']['malicious']} vendors"
        elif result["data"]["suspicious"] > 0:
            result["data"]["flag"] = f"flagged suspicious by {result['data']['suspicious']} vendors"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"virustotal failed for {domain}: {e}")

    return result
