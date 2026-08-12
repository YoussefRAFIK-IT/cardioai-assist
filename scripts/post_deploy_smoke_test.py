from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


def request_json(url: str, method: str = "GET", api_key: str | None = None):
    req = urllib.request.Request(url, method=method)
    if api_key:
        req.add_header("X-API-Key", api_key)
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} sur {url}: {body}") from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="https://cardioai-assist.onrender.com")
    parser.add_argument("--api-key", default=os.getenv("API_KEY"))
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")

    status, health = request_json(base + "/api/v1/health")
    print("HEALTH", status)
    print(json.dumps(health, indent=2, ensure_ascii=False))

    if status != 200 or health.get("status") != "ok":
        raise SystemExit("Health check non valide.")

    model = health.get("model", {})
    if model.get("configured_mode") != "REAL_RAW_ENSEMBLE":
        raise SystemExit("L'application n'est pas en REAL_RAW_ENSEMBLE.")
    if model.get("real_bundle_ready") is not True:
        raise SystemExit("Le bundle réel n'est pas prêt.")

    if args.warmup:
        if not args.api_key:
            raise SystemExit("--warmup nécessite --api-key ou API_KEY.")
        status, warmed = request_json(
            base + "/api/v1/warmup",
            method="POST",
            api_key=args.api_key,
        )
        print("WARMUP", status)
        print(json.dumps(warmed, indent=2, ensure_ascii=False))
        if status != 200 or warmed.get("warmed") is not True:
            raise SystemExit("Warm-up non valide.")

    print("SMOKE TEST DEPLOIEMENT : PASS")


if __name__ == "__main__":
    main()
