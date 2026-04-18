import logging
import dns.resolver
import socket
import concurrent.futures

log = logging.getLogger(__name__)

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "smtp", "pop", "imap", "webmail", "remote",
    "vpn", "api", "dev", "staging", "test", "admin", "portal", "shop",
    "blog", "cdn", "static", "assets", "m", "mobile", "app", "auth",
    "login", "secure", "dashboard", "git", "gitlab", "jenkins", "jira",
    "confluence", "docs", "support", "helpdesk", "status", "monitor",
    "ns1", "ns2", "mx1", "mx2", "smtp1", "smtp2", "backup", "db",
    "database", "mysql", "postgres", "redis", "elastic", "kibana",
]


def resolve_records(domain):
    records = {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 3

    for rtype in RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, rtype)
            records[rtype] = [str(r) for r in answers]
        except Exception:
            records[rtype] = []

    return records


def probe_subdomain(subdomain, domain):
    fqdn = f"{subdomain}.{domain}"
    try:
        ip = socket.gethostbyname(fqdn)
        return {"subdomain": fqdn, "ip": ip}
    except Exception:
        return None


def bruteforce_subdomains(domain, wordlist=None):
    words = wordlist if wordlist else COMMON_SUBDOMAINS
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        futures = {pool.submit(probe_subdomain, w, domain): w for w in words}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                found.append(res)
    return found


def run(domain):
    result = {"module": "dns", "domain": domain, "status": "ok", "data": {}}

    try:
        result["data"]["records"] = resolve_records(domain)
        result["data"]["subdomains"] = bruteforce_subdomains(domain)
        result["data"]["subdomain_count"] = len(result["data"]["subdomains"])
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log.warning(f"dns failed for {domain}: {e}")

    return result
