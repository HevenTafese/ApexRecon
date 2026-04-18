import logging
import requests
import time

log = logging.getLogger(__name__)

HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"


def check_email(email, api_key):
    try:
        resp = requests.get(
            HIBP_URL.format(email),
            headers={"hibp-api-key": api_key, "User-Agent": "ApexRecon"},
            params={"truncateResponse": "false"},
            timeout=10
        )
        if resp.status_code == 404:
            return {"email": email, "breached": False, "breaches": []}
        if resp.status_code == 429:
            time.sleep(2)
            return check_email(email, api_key)
        resp.raise_for_status()
        breaches = resp.json()
        return {
            "email":    email,
            "breached": True,
            "count":    len(breaches),
            "breaches": [
                {
                    "name":         b.get("Name"),
                    "domain":       b.get("Domain"),
                    "breach_date":  b.get("BreachDate"),
                    "data_classes": b.get("DataClasses", []),
                }
                for b in breaches
            ],
        }
    except Exception as e:
        return {"email": email, "breached": None, "error": str(e)}


def run(emails, api_key=None):
    result = {"module": "hibp", "status": "ok", "data": {}}

    if not api_key:
        result["status"] = "skipped"
        result["reason"] = "no api key"
        return result

    if not emails:
        result["status"] = "skipped"
        result["reason"] = "no emails to check"
        return result

    checks = []
    for email in emails[:10]:
        checks.append(check_email(email, api_key))
        time.sleep(1.5)

    result["data"] = {
        "results":        checks,
        "breached_count": sum(1 for c in checks if c.get("breached")),
        "total_checked":  len(checks),
    }

    return result
