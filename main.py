import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

ROOT = Path(__file__).parent


def main():
    p = argparse.ArgumentParser(description="ApexRecon — attack surface reconnaissance")
    p.add_argument("--scan", metavar="DOMAIN", help="run a headless scan and save report")
    p.add_argument("--shodan", metavar="KEY",  help="Shodan API key")
    p.add_argument("--vt",     metavar="KEY",  help="VirusTotal API key")
    p.add_argument("--hibp",   metavar="KEY",  help="HIBP API key")
    args = p.parse_args()

    if args.scan:
        from core.scanner import run_scan
        config = {
            "shodan_key": args.shodan,
            "vt_key":     args.vt,
            "hibp_key":   args.hibp,
        }
        results = run_scan(args.scan, config)
        print(f"\nscan complete: {results['target']}")
        print(f"risk level:    {results['summary']['risk_level'].upper()}")
        print(f"flags:         {results['summary']['flag_count']}")
        print(f"duration:      {results['duration_s']}s")
        if results["summary"]["flags"]:
            print("\nflags raised:")
            for f in results["summary"]["flags"]:
                print(f"  - {f}")
        return

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(ROOT / "dashboard" / "app.py"),
        "--server.headless", "true",
    ])


if __name__ == "__main__":
    main()
