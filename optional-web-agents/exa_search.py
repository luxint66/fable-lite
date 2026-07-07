#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

ENV_FILE = os.path.expanduser("~/.config/agent-browser-lite/env")


def _load_key_from_env_file() -> Optional[str]:
    """Read EXA_API_KEY from the agent-browser-lite env file, so the caller
    never has to source it into the shell (that step is where callers fumble)."""
    try:
        with open(ENV_FILE) as fh:
            for raw in fh:
                line = raw.strip()
                if line.startswith("EXA_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def exa_search(
    query: str,
    api_key: Optional[str] = None,
    search_type: str = "auto",
    num_results: int = 10,
    contents: Optional[Dict] = None,
    max_retries: int = 5,
    backoff_base: float = 2.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Perform a search using Exa's /search endpoint, billed against the
    account's normal prepaid balance via the x-api-key header.

    Exa intermittently misroutes some requests onto an x402 crypto-payment
    challenge even when the key/balance are fine (a server-side routing bug,
    not something a client can force around). Retries with exponential
    backoff specifically on that tag before giving up.
    """
    if not api_key:
        api_key = os.getenv("EXA_API_KEY") or _load_key_from_env_file()
        if not api_key:
            raise ValueError(
                f"API key not found: pass --api-key, set EXA_API_KEY, or add it to {ENV_FILE}"
            )

    url = "https://api.exa.ai/search"

    payload = {
        "query": query,
        "type": search_type,
        "numResults": num_results,
        **kwargs
    }
    if contents:
        payload["contents"] = contents

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    if max_retries < 1:
        raise ValueError("max_retries must be at least 1")

    delay = backoff_base
    response = None
    for attempt in range(max_retries):
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()

        tag = None
        try:
            tag = response.json().get("tag")
        except ValueError:
            pass

        if tag != "X402_PAYMENT_REQUIRED" or attempt == max_retries - 1:
            break
        time.sleep(delay)
        delay *= 2

    assert response is not None
    print(f"Status: {response.status_code}", file=sys.stderr)
    print(response.text[:1000], file=sys.stderr)  # truncate for safety
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Query the Exa /search API with x402 retry.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--type", default="auto")
    parser.add_argument("--num-results", type=int, default=5)
    parser.add_argument("--highlights", action="store_true", help="Request highlights in contents.")
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    contents = {"highlights": True} if args.highlights else None

    try:
        result = exa_search(
            args.query,
            api_key=args.api_key,
            search_type=args.type,
            num_results=args.num_results,
            contents=contents,
        )
    except (requests.HTTPError, ValueError) as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
