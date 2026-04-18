import logging
import requests

log = logging.getLogger(__name__)

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "X-XSS-Protection",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
]


def grade(missing_count, total):
    ratio = missing_count / total
    if ratio == 0:       return "A"
    elif ratio <= 0.2:   return "B"
    elif ratio <= 0.4:   return "C"
    elif ratio <= 0.6:   return "D"
    else:                return "F"


def run(domain):
    result = {"module": "headers", "domain": domain, "status": "ok", "data": {}}

    for scheme in ["https", "http"]:
        try:
            resp = requests.get(f"{scheme}://{domain}", timeout=10, allow_redirects=True, verify=False)
            headers = dict(resp.headers)

            present = {}
            missing = []
            for h in SECURITY_HEADERS:
                if h.lower() in {k.lower(): v for k, v in headers.items()}:
                    present[h] = headers.get(h, "present")
                else:
                    missing.append(h)

            server  = headers.get("Server", headers.get("server"))
            powered = headers.get("X-Powered-By", headers.get("x-powered-by"))

            result["data"] = {
                "url":             resp.url,
                "status_code":     resp.status_code,
                "scheme":          scheme,
                "server":          server,
                "x_powered_by":    powered,
                "present_headers": present,
                "missing_headers": missing,
                "grade":           grade(len(missing), len(SECURITY_HEADERS)),
                "flags":           [],
            }

            if server:
                result["data"]["flags"].append(f"server header exposes: {server}")
            if powered:
                result["data"]["flags"].append(f"x-powered-by exposes: {powered}")

            return result

        except requests.exceptions.SSLError:
            continue
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            log.warning(f"headers failed for {domain}: {e}")
            return result

    return result
