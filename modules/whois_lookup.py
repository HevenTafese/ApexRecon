import logging
import whois
from datetime import datetime

log = logging.getLogger(__name__)


def run(domain):
    result = {"module": "whois", "domain": domain, "status": "ok", "data": {}}

    try:
        w = whois.whois(domain)

        def to_str(val):
            if isinstance(val, list):
                return [str(v) for v in val]
            return str(val) if val else None

        def to_date(val):
            if isinstance(val, list):
                val = val[0]
            if isinstance(val, datetime):
                return val.strftime("%Y-%m-%d")
            return str(val) if val else None

        result["data"] = {
            "registrar":          to_str(w.registrar),
            "registrant_org":     to_str(w.org),
            "registrant_country": to_str(w.country),
            "creation_date":      to_date(w.creation_date),
            "expiry_date":        to_date(w.expiration_date),
            "updated_date":       to_date(w.updated_date),
            "name_servers":       to_str(w.name_servers) if w.name_servers else [],
            "status":             to_str(w.status) if w.status else [],
            "emails":             to_str(w.emails) if w.emails else [],
            "dnssec":             to_str(w.dnssec),
        }

        if w.creation_date:
            cd = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
            if isinstance(cd, datetime):
                age = (datetime.now() - cd).days
                result["data"]["domain_age_days"] = age
                if age < 90:
                    result["data"]["flag"] = "recently registered domain"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"whois failed for {domain}: {e}")

    return result
