import logging
import json
from pathlib import Path
from datetime import datetime

from modules import whois_lookup, dns_enum, cert_log, shodan_scan
from modules import virustotal_check, header_audit, geoip, hibp_check

log = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def run_scan(domain, config=None):
    config  = config or {}
    started = datetime.now()

    results = {
        "target":     domain,
        "started_at": started.isoformat(),
        "modules":    {},
    }

    steps = [
        ("whois",      lambda: whois_lookup.run(domain)),
        ("dns",        lambda: dns_enum.run(domain)),
        ("certlog",    lambda: cert_log.run(domain)),
        ("geoip",      lambda: geoip.run(domain)),
        ("headers",    lambda: header_audit.run(domain)),
        ("shodan",     lambda: shodan_scan.run(domain, config.get("shodan_key"))),
        ("virustotal", lambda: virustotal_check.run(domain, config.get("vt_key"))),
    ]

    for name, fn in steps:
        try:
            results["modules"][name] = fn()
        except Exception as e:
            log.warning(f"module {name} failed: {e}")
            results["modules"][name] = {"module": name, "status": "error", "error": str(e)}

    emails = results["modules"].get("whois", {}).get("data", {}).get("emails", [])
    if isinstance(emails, str):
        emails = [emails]
    emails = [e for e in (emails or []) if isinstance(e, str) and "@" in e]

    try:
        results["modules"]["hibp"] = hibp_check.run(emails, config.get("hibp_key"))
    except Exception as e:
        results["modules"]["hibp"] = {"module": "hibp", "status": "error", "error": str(e)}

    results["finished_at"] = datetime.now().isoformat()
    results["duration_s"]  = round((datetime.now() - started).total_seconds(), 2)
    results["summary"]     = build_summary(results)

    save_report(domain, results)
    return results


def build_summary(results):
    mods    = results["modules"]
    summary = {"flags": [], "stats": {}}

    if mods.get("whois", {}).get("data", {}).get("flag"):
        summary["flags"].append(mods["whois"]["data"]["flag"])

    summary["stats"]["subdomains_dns"]  = mods.get("dns", {}).get("data", {}).get("subdomain_count", 0)
    summary["stats"]["subdomains_cert"] = mods.get("certlog", {}).get("data", {}).get("subdomain_count", 0)
    summary["stats"]["certificates"]    = mods.get("certlog", {}).get("data", {}).get("cert_count", 0)
    summary["stats"]["open_ports"]      = len(mods.get("shodan", {}).get("data", {}).get("open_ports", []))
    summary["stats"]["headers_grade"]   = mods.get("headers", {}).get("data", {}).get("grade", "N/A")
    summary["stats"]["missing_headers"] = len(mods.get("headers", {}).get("data", {}).get("missing_headers", []))

    if mods.get("shodan", {}).get("data", {}).get("vulns"):
        summary["flags"].append(f"{len(mods['shodan']['data']['vulns'])} CVEs found via Shodan")

    if mods.get("virustotal", {}).get("data", {}).get("flag"):
        summary["flags"].append(mods["virustotal"]["data"]["flag"])

    if mods.get("headers", {}).get("data", {}).get("flags"):
        summary["flags"].extend(mods["headers"]["data"]["flags"])

    if mods.get("hibp", {}).get("data", {}).get("breached_count", 0) > 0:
        summary["flags"].append(f"{mods['hibp']['data']['breached_count']} email(s) found in breach databases")

    summary["flag_count"] = len(summary["flags"])
    summary["risk_level"] = (
        "high"   if summary["flag_count"] >= 4 else
        "medium" if summary["flag_count"] >= 2 else
        "low"
    )

    return summary


def save_report(domain, results):
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{domain.replace('.','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(results, indent=2, default=str))
    log.info(f"report saved: {path}")
    return path
