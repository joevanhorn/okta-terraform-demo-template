#!/usr/bin/env python3
"""
session_replayer.py

Replays an Okta session cookie from a different context (IP, User-Agent, geo)
to trigger Okta's session hijacking detection. This represents the "attacker"
side of a session hijacking simulation.

Can run as:
1. A standalone script (for local testing or EC2 execution)
2. An importable module (for use by trigger_itp_demo.py)
3. An AWS Lambda handler (for cross-region replay)

Usage (standalone):
    python3 -m itp.session_replayer \
        --cookie "IDX_COOKIE_VALUE" \
        --domain "myorg.okta.com"

Usage (Lambda):
    # Invoked by trigger_itp_demo.py with payload:
    # {"cookie_name": "idx", "cookie": "...", "okta_domain": "myorg.okta.com"}
"""

import os
import sys
import json
import argparse
from typing import Dict

# Use requests if available, fall back to urllib for Lambda
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error
    import http.cookiejar


# Attacker User-Agents — deliberately different from the victim's macOS Chrome
ATTACKER_USER_AGENTS = [
    # Windows Chrome
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    # Linux Firefox
    (
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    # Windows Edge
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
]


def replay_cookie(cookie_name: str, cookie_value: str, okta_domain: str,
                  user_agent_index: int = 0) -> Dict:
    """
    Replay a session cookie against Okta from the current context.

    The fact that this runs from a different IP and User-Agent than the
    original session is what triggers Okta's session hijacking detection.

    Args:
        cookie_name: Cookie name (typically "idx" or "sid")
        cookie_value: The session cookie value
        okta_domain: Full Okta domain (e.g., "myorg.okta.com")
        user_agent_index: Which attacker UA to use (0-2)

    Returns:
        Dict with status, http_code, and details
    """
    url = f"https://{okta_domain}/app/UserHome"
    ua = ATTACKER_USER_AGENTS[user_agent_index % len(ATTACKER_USER_AGENTS)]

    print(f"  Replaying {cookie_name} cookie against {okta_domain}...")
    print(f"  User-Agent: {ua[:60]}...")
    print(f"  Target URL: {url}")

    if HAS_REQUESTS:
        return _replay_with_requests(url, cookie_name, cookie_value, okta_domain, ua)
    else:
        return _replay_with_urllib(url, cookie_name, cookie_value, okta_domain, ua)


def _replay_with_requests(url: str, cookie_name: str, cookie_value: str,
                          okta_domain: str, user_agent: str) -> Dict:
    """Replay using requests library"""
    try:
        response = requests.get(
            url,
            cookies={cookie_name: cookie_value},
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            allow_redirects=False,
            timeout=15,
        )

        result = {
            "status": "success",
            "http_code": response.status_code,
            "redirect_url": response.headers.get("Location", ""),
            "content_length": len(response.content),
        }

        if response.status_code in (200, 302):
            print(f"  Cookie accepted (HTTP {response.status_code})")
            if response.status_code == 302:
                print(f"     Redirect: {result['redirect_url']}")
        elif response.status_code == 401:
            print(f"  Cookie rejected (HTTP 401) — session may have been revoked")
        else:
            print(f"  Unexpected response: HTTP {response.status_code}")

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}


def _replay_with_urllib(url: str, cookie_name: str, cookie_value: str,
                        okta_domain: str, user_agent: str) -> Dict:
    """Replay using stdlib urllib (for Lambda without requests layer)"""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", user_agent)
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        req.add_header("Cookie", f"{cookie_name}={cookie_value}")

        # Don't follow redirects
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)

        try:
            response = opener.open(req, timeout=15)
            http_code = response.getcode()
            content_length = len(response.read())
            redirect_url = ""
        except urllib.error.HTTPError as e:
            http_code = e.code
            content_length = 0
            redirect_url = e.headers.get("Location", "")

        result = {
            "status": "success",
            "http_code": http_code,
            "redirect_url": redirect_url,
            "content_length": content_length,
        }

        print(f"  Cookie replay result: HTTP {http_code}")
        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}


# --- AWS Lambda Handler ---

def handler(event, context):
    """
    AWS Lambda handler for cross-region cookie replay.

    Event payload:
        {
            "cookie_name": "idx",
            "cookie": "COOKIE_VALUE",
            "okta_domain": "myorg.okta.com",
            "user_agent_index": 0
        }
    """
    cookie_name = event.get("cookie_name", "idx")
    cookie_value = event.get("cookie")
    okta_domain = event.get("okta_domain")
    ua_index = event.get("user_agent_index", 0)

    if not cookie_value or not okta_domain:
        return {
            "status": "error",
            "error": "cookie and okta_domain are required"
        }

    result = replay_cookie(cookie_name, cookie_value, okta_domain, ua_index)

    # Add Lambda context info
    if context:
        result["lambda_region"] = context.invoked_function_arn.split(":")[3]
        result["lambda_request_id"] = context.aws_request_id

    return result


# --- Standalone CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Replay Okta session cookie from attacker context"
    )
    parser.add_argument("--cookie-name", default="idx", help="Cookie name (default: idx)")
    parser.add_argument("--cookie", required=True, help="Session cookie value")
    parser.add_argument("--domain", required=True, help="Okta domain (e.g., myorg.okta.com)")
    parser.add_argument("--ua-index", type=int, default=0, help="User-Agent index (0-2)")
    parser.add_argument("--output", help="Write result JSON to file")

    args = parser.parse_args()

    result = replay_cookie(args.cookie_name, args.cookie, args.domain, args.ua_index)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)

    print(f"\nResult: {json.dumps(result, indent=2)}")
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
