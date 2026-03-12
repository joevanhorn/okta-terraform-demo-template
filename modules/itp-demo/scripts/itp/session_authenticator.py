#!/usr/bin/env python3
"""
session_authenticator.py

Authenticates to Okta using a headless browser (Playwright) and captures
the IDX session cookie. This represents the "victim" side of a session
hijacking simulation.

Requirements:
    pip install playwright pyotp
    playwright install chromium

Usage (as module):
    from itp.session_authenticator import SessionAuthenticator
    auth = SessionAuthenticator("taskvantage", "okta.com")
    result = auth.authenticate("user@example.com", "password", totp_secret="BASE32SECRET")
    print(result["cookie"])  # IDX cookie value

Usage (standalone):
    python3 -m itp.session_authenticator \
        --username user@example.com \
        --password-ssm /taskvantage-prod/itp-demo/password \
        --totp-ssm /taskvantage-prod/itp-demo/totp-secret
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Optional


class AuthenticationError(Exception):
    """Raised when browser authentication fails."""

    def __init__(self, message, video_path=None):
        super().__init__(message)
        self.video_path = video_path


class BrowserSession:
    """Wraps an open Playwright browser session for continuous video recording.

    Keeps the browser alive so the video captures the full demo flow:
    login -> dashboard -> attacker replay -> ULO session termination.
    """

    # URL patterns that indicate the session has been terminated
    LOGIN_URL_PATTERNS = ["/login/", "/signin/", "/login/login.htm"]
    SESSION_EXPIRED_TEXT = ["session expired", "signed out", "session has ended"]

    def __init__(self, pw, browser, context, page, auth_result: Dict,
                 owns_pw: bool = True):
        self._pw = pw
        self._browser = browser
        self._context = context
        self._page = page
        self._auth_result = auth_result
        self._owns_pw = owns_pw  # Only stop pw on close if we own it
        self._closed = False

    @property
    def cookie_name(self) -> str:
        return self._auth_result["cookie_name"]

    @property
    def cookie(self) -> str:
        return self._auth_result["cookie"]

    @property
    def domain(self) -> str:
        return self._auth_result["domain"]

    @property
    def auth_result(self) -> Dict:
        return self._auth_result

    @property
    def page(self):
        return self._page

    def wait_for_session_termination(self, timeout: int = 120,
                                     poll_interval: int = 5) -> Dict:
        """Reload the page periodically, watching for session termination.

        Returns dict with terminated (bool), elapsed (int), final_url (str).
        """
        print(f"  Watching browser for session termination ({timeout}s, every {poll_interval}s)...")
        start = time.time()

        while time.time() - start < timeout:
            time.sleep(poll_interval)
            elapsed = int(time.time() - start)

            try:
                self._page.reload(wait_until="domcontentloaded", timeout=15000)
            except Exception as e:
                # Navigation failure may itself indicate session invalidation
                print(f"  [{elapsed}s] Page reload failed: {e}")
                return {
                    "terminated": True,
                    "elapsed": elapsed,
                    "final_url": self._page.url,
                    "reason": f"reload_error: {e}",
                }

            current_url = self._page.url.lower()

            # Check URL for login redirect
            for pattern in self.LOGIN_URL_PATTERNS:
                if pattern in current_url:
                    print(f"  [{elapsed}s] Session terminated — redirected to login")
                    # Wait a moment to let the login page render for the video
                    time.sleep(3)
                    return {
                        "terminated": True,
                        "elapsed": elapsed,
                        "final_url": self._page.url,
                        "reason": "login_redirect",
                    }

            # Fallback: check page content for session-expired text
            try:
                body_text = self._page.text_content("body", timeout=3000) or ""
                body_lower = body_text.lower()
                for text in self.SESSION_EXPIRED_TEXT:
                    if text in body_lower:
                        print(f"  [{elapsed}s] Session terminated — page says '{text}'")
                        time.sleep(3)
                        return {
                            "terminated": True,
                            "elapsed": elapsed,
                            "final_url": self._page.url,
                            "reason": f"page_content: {text}",
                        }
            except Exception:
                pass

            print(f"  [{elapsed}s] Session still active — {self._page.url}")

        print(f"  Timeout reached ({timeout}s) — session was NOT terminated")
        return {
            "terminated": False,
            "elapsed": timeout,
            "final_url": self._page.url,
            "reason": "timeout",
        }

    def close(self) -> Optional[str]:
        """Close browser and finalize video. Returns video file path or None."""
        if self._closed:
            return None
        self._closed = True

        video_path = None
        try:
            if self._page.video:
                video_path = self._page.video.path()
        except Exception:
            pass

        try:
            self._context.close()
        except Exception:
            pass
        try:
            self._browser.close()
        except Exception:
            pass
        if self._owns_pw:
            try:
                self._pw.stop()
            except Exception:
                pass

        if video_path:
            print(f"  Video saved: {video_path}")
        return str(video_path) if video_path else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def get_ssm_parameter(name: str, region: str = "us-east-2", profile: str = None) -> str:
    """Retrieve a parameter from AWS SSM Parameter Store"""
    import boto3
    session_kwargs = {}
    if profile:
        session_kwargs["profile_name"] = profile
    session = boto3.Session(region_name=region, **session_kwargs)
    ssm = session.client("ssm")

    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]


class SessionAuthenticator:
    """Authenticates to Okta and captures session cookies"""

    # Victim user-agent (Mac Chrome — distinct from attacker UAs)
    VICTIM_UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Attacker user-agent (Windows Firefox — visibly different from victim)
    ATTACKER_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
        "Gecko/20100101 Firefox/121.0"
    )

    def __init__(self, org_name: str, base_url: str = "okta.com"):
        self.org_name = org_name
        self.base_url = base_url
        self.okta_url = f"https://{org_name}.{base_url}"

    def authenticate(self, username: str, password: str,
                     totp_secret: Optional[str] = None,
                     timeout: int = 30000,
                     record_video: Optional[str] = None) -> Dict:
        """
        Authenticate to Okta and capture session cookie.

        Prefers browser-based auth (captures idx cookie needed for ITP).
        Falls back to API-based auth (captures sid only) if browser fails.

        Args:
            record_video: Directory path to save video recording of the browser
                          session. If None, no video is recorded.
        """
        # Try browser-based auth first (captures idx — required for ITP detection)
        result = self._authenticate_via_browser(
            username, password, totp_secret, timeout, record_video=record_video
        )
        if result["status"] == "success":
            return result

        print("  Browser auth failed, falling back to API-based auth...")
        api_result = self._authenticate_via_api(username, password, totp_secret)
        # Preserve video_path from the browser attempt (video was saved even on failure)
        if result.get("video_path") and not api_result.get("video_path"):
            api_result["video_path"] = result["video_path"]
        return api_result

    def _authenticate_via_api(self, username: str, password: str,
                               totp_secret: Optional[str] = None) -> Dict:
        """
        Authenticate via Okta Authn API and capture session cookie via redirect.

        This approach:
        1. POST to /api/v1/authn to get a sessionToken
        2. Handle MFA if required (TOTP via /api/v1/authn/factors/{id}/verify)
        3. Exchange sessionToken for sid cookie via /login/sessionCookieRedirect
        """
        import requests as req

        print(f"Authenticating as {username} to {self.okta_url} (API mode)...")

        # Step 1: Primary authentication
        print("  Authenticating with Authn API...")
        authn_resp = req.post(
            f"{self.okta_url}/api/v1/authn",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        if authn_resp.status_code != 200:
            error = authn_resp.json().get("errorSummary", authn_resp.text)
            print(f"  Authentication failed: {error}")
            return {"status": "error", "error": error}

        authn_data = authn_resp.json()
        status = authn_data.get("status")

        # Step 2: Handle MFA if needed
        if status == "MFA_REQUIRED":
            if not totp_secret:
                return {"status": "error", "error": "MFA required but no TOTP secret provided"}

            try:
                import pyotp
            except ImportError:
                return {"status": "error", "error": "pyotp not installed"}

            state_token = authn_data["stateToken"]
            factors = authn_data.get("_embedded", {}).get("factors", [])

            # Find TOTP factor
            totp_factor = None
            for f in factors:
                if f.get("factorType") == "token:software:totp":
                    totp_factor = f
                    break

            if not totp_factor:
                return {"status": "error", "error": "No TOTP factor enrolled"}

            print("  Verifying TOTP factor...")
            code = pyotp.TOTP(totp_secret).now()
            verify_url = totp_factor["_links"]["verify"]["href"]
            verify_resp = req.post(
                verify_url,
                json={"stateToken": state_token, "passCode": code},
                headers={"Content-Type": "application/json"},
            )

            if verify_resp.status_code != 200:
                error = verify_resp.json().get("errorSummary", verify_resp.text)
                return {"status": "error", "error": f"MFA verification failed: {error}"}

            authn_data = verify_resp.json()
            status = authn_data.get("status")

        if status != "SUCCESS":
            return {"status": "error", "error": f"Unexpected auth status: {status}"}

        session_token = authn_data["sessionToken"]
        print(f"  Got session token ({len(session_token)} chars)")

        # Step 3: Exchange sessionToken for session cookie
        print("  Exchanging token for session cookie...")
        redirect_url = (
            f"{self.okta_url}/login/sessionCookieRedirect"
            f"?token={session_token}"
            f"&redirectUrl={self.okta_url}/app/UserHome"
        )

        session = req.Session()
        session.headers.update({"User-Agent": self.VICTIM_UA})
        resp = session.get(redirect_url, allow_redirects=True)

        # Extract sid cookie from session
        sid = session.cookies.get("sid", domain=f"{self.org_name}.{self.base_url}")
        if not sid:
            # Try without domain filter
            for cookie in session.cookies:
                if cookie.name == "sid":
                    sid = cookie.value
                    break

        if not sid:
            print("  No sid cookie found in response")
            return {"status": "error", "error": "No sid cookie after redirect"}

        result = {
            "status": "success",
            "cookie_name": "sid",
            "cookie": sid,
            "domain": f"{self.org_name}.{self.base_url}",
            "user_agent": self.VICTIM_UA,
            "url": str(resp.url),
        }

        print(f"  Captured sid cookie ({len(sid)} chars)")
        print(f"     Domain: {result['domain']}")
        return result

    def _do_browser_login(self, page, context, username: str, password: str,
                          totp_secret: Optional[str] = None) -> Optional[Dict]:
        """Shared browser login logic: username -> password -> TOTP -> cookie capture.

        Returns the captured cookie dict (from Playwright's context.cookies())
        or None if no session cookie was found.
        """
        # Navigate to Okta login
        print("  Navigating to login page...")
        page.goto(self.okta_url)

        # Wait for and fill username
        print("  Entering username...")
        page.wait_for_selector('input[name="identifier"]', state="visible")
        page.fill('input[name="identifier"]', username)
        page.click('input[type="submit"], button[type="submit"]')

        # Wait for password field or authenticator selection
        print("  Waiting for password prompt...")
        page.wait_for_selector(
            'input[name="credentials.passcode"], input[type="password"], '
            '[data-se="okta_password"]',
            state="visible",
            timeout=10000
        )

        # OIE flow: authenticator selection screen — click "Select" next to Password
        password_select = page.query_selector('[data-se="okta_password"]')
        if password_select:
            print("  Selecting Password authenticator...")
            select_btn = password_select.query_selector('button, [data-se="select-button"]')
            if select_btn:
                select_btn.click()
            else:
                password_select.click()
            page.wait_for_selector(
                'input[name="credentials.passcode"], input[type="password"]',
                state="visible"
            )

        print("  Entering password...")
        password_input = page.query_selector(
            'input[name="credentials.passcode"]'
        ) or page.query_selector('input[type="password"]')
        password_input.fill(password)
        page.click('input[type="submit"], button[type="submit"]')

        # Handle TOTP MFA if secret provided
        if totp_secret:
            self._handle_totp(page, totp_secret)

        # Wait for idx cookie to appear (set during OAuth redirect)
        print("  Waiting for authentication to complete...")
        idx_cookie = None
        for i in range(30):
            time.sleep(1)
            cookies = context.cookies()
            for cookie in cookies:
                if cookie["name"] == "idx":
                    idx_cookie = cookie
                    break
            if idx_cookie:
                print(f"  idx cookie captured after {i+1}s")
                break
            current_url = page.url
            if "/enduser/" in current_url or "/app/UserHome" in current_url:
                # On dashboard but no idx yet — grab what we can
                for name in ["sid", "JSESSIONID"]:
                    for cookie in cookies:
                        if cookie["name"] == name:
                            idx_cookie = cookie
                            break
                    if idx_cookie:
                        break
                break

        if not idx_cookie:
            cookies = context.cookies()
            print("  No IDX/SID cookie found. Available cookies:")
            for c in cookies:
                print(f"     {c['name']}: {c['domain']}")
            return None

        print(f"  Captured {idx_cookie['name']} cookie ({len(idx_cookie['value'])} chars)")
        print(f"     Domain: {idx_cookie['domain']}")
        return idx_cookie

    def _handle_totp(self, page, totp_secret: str):
        """Handle TOTP MFA challenge in the browser."""
        print("  Handling TOTP MFA challenge...")
        import pyotp

        totp = pyotp.TOTP(totp_secret)

        # Wait for old password field to disappear, then TOTP field to appear
        # OIE reuses 'credentials.passcode' for password but uses
        # 'credentials.totp' for the TOTP code input
        try:
            page.wait_for_selector(
                'input[name="credentials.passcode"]',
                state="hidden",
                timeout=5000
            )
        except Exception:
            pass  # May already be gone

        # Now wait for the TOTP input or authenticator selection
        page.wait_for_selector(
            'input[name="credentials.totp"], '
            '[data-se="okta_verify-totp"]',
            state="visible",
            timeout=15000
        )

        # If we see the authenticator selector, click it first
        totp_select = page.query_selector('[data-se="okta_verify-totp"]')
        if totp_select:
            print("  Selecting Okta Verify TOTP authenticator...")
            select_btn = totp_select.query_selector('button, [data-se="select-button"]')
            if select_btn:
                select_btn.click()
            else:
                totp_select.click()
            page.wait_for_selector(
                'input[name="credentials.totp"]',
                state="visible",
                timeout=10000
            )

        code = totp.now()
        print(f"  Entering TOTP code: {code}")

        # Fill the TOTP input
        totp_input = page.query_selector('input[name="credentials.totp"]')
        if totp_input:
            totp_input.fill(code)
        else:
            # Fallback: find any visible text/tel input (not identifier)
            for inp in page.query_selector_all('input'):
                inp_type = inp.evaluate('el => el.type')
                inp_vis = inp.evaluate('el => el.offsetParent !== null')
                inp_name = inp.evaluate('el => el.name')
                if inp_vis and inp_type in ('text', 'tel', 'number') and inp_name != 'identifier':
                    print(f"  Fallback: filling input name={inp_name!r}")
                    inp.fill(code)
                    break

        page.click('input[type="submit"], button[type="submit"], button[data-type="save"]')

    def _authenticate_via_browser(self, username: str, password: str,
                                   totp_secret: Optional[str] = None,
                                   timeout: int = 30000,
                                   record_video: Optional[str] = None) -> Dict:
        """Authenticate via Playwright headless browser.

        Args:
            record_video: Directory path to save video recording. If provided,
                          Playwright records the browser session as a .webm file.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Error: playwright is required. Install with:")
            print("  pip install playwright && playwright install chromium")
            return {"status": "error", "error": "playwright not installed"}

        print(f"Authenticating as {username} to {self.okta_url}...")
        if record_video:
            print(f"  Recording video to: {record_video}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context_opts = {"user_agent": self.VICTIM_UA}
            if record_video:
                os.makedirs(record_video, exist_ok=True)
                context_opts["record_video_dir"] = record_video
                context_opts["record_video_size"] = {"width": 1280, "height": 720}
            context = browser.new_context(**context_opts)
            page = context.new_page()
            page.set_default_timeout(timeout)

            try:
                idx_cookie = self._do_browser_login(
                    page, context, username, password, totp_secret
                )

                if not idx_cookie:
                    video_path = None
                    if record_video:
                        try:
                            if page.video:
                                video_path = page.video.path()
                        except Exception:
                            pass
                    context.close()
                    browser.close()
                    if video_path:
                        print(f"  Video saved: {video_path}")
                    return {
                        "status": "error",
                        "error": "Session cookie not found",
                        "video_path": str(video_path) if video_path else None,
                    }

                result = {
                    "status": "success",
                    "cookie_name": idx_cookie["name"],
                    "cookie": idx_cookie["value"],
                    "domain": idx_cookie["domain"],
                    "user_agent": self.VICTIM_UA,
                    "url": page.url,
                }

                # Save video before closing (Playwright finalizes on context.close)
                video_path = None
                if record_video and page.video:
                    video_path = page.video.path()
                context.close()
                browser.close()
                if video_path:
                    print(f"  Video saved: {video_path}")
                    result["video_path"] = str(video_path)
                return result

            except Exception as e:
                print(f"  Authentication failed: {e}")
                try:
                    page.screenshot(path="/tmp/itp-auth-failure.png")
                    print("     Screenshot saved to /tmp/itp-auth-failure.png")
                except Exception:
                    pass
                video_path = None
                if record_video:
                    try:
                        if page.video:
                            video_path = page.video.path()
                    except Exception:
                        pass
                context.close()
                browser.close()
                if video_path:
                    print(f"  Video saved: {video_path}")
                return {
                    "status": "error",
                    "error": str(e),
                    "video_path": str(video_path) if video_path else None,
                }

    def authenticate_persistent(self, username: str, password: str,
                                totp_secret: Optional[str] = None,
                                timeout: int = 30000,
                                record_video: Optional[str] = None) -> "BrowserSession":
        """Authenticate and return a BrowserSession with the browser still open.

        Unlike authenticate(), the browser stays open so the video captures
        the full demo: login -> dashboard -> attacker replay -> ULO termination.

        Args:
            record_video: Directory path for video recording (required for
                          continuous video capture).

        Returns:
            BrowserSession wrapping the open browser.

        Raises:
            AuthenticationError: If browser auth fails.
            ImportError: If playwright is not installed.
        """
        from playwright.sync_api import sync_playwright

        print(f"Authenticating as {username} to {self.okta_url} (persistent session)...")
        if record_video:
            print(f"  Recording video to: {record_video}")

        # Start Playwright without context manager so it stays alive
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        context_opts = {"user_agent": self.VICTIM_UA}
        if record_video:
            os.makedirs(record_video, exist_ok=True)
            context_opts["record_video_dir"] = record_video
            context_opts["record_video_size"] = {"width": 1280, "height": 720}
        context = browser.new_context(**context_opts)
        page = context.new_page()
        page.set_default_timeout(timeout)

        try:
            idx_cookie = self._do_browser_login(
                page, context, username, password, totp_secret
            )

            if not idx_cookie:
                # Clean up and raise
                video_path = None
                try:
                    if page.video:
                        video_path = page.video.path()
                except Exception:
                    pass
                context.close()
                browser.close()
                pw.stop()
                raise AuthenticationError(
                    "Session cookie not found",
                    video_path=str(video_path) if video_path else None,
                )

            # Navigate to dashboard and let it render
            print("  Navigating to dashboard...")
            try:
                page.goto(f"{self.okta_url}/app/UserHome", wait_until="domcontentloaded")
                time.sleep(2)
                print(f"  Dashboard loaded: {page.url}")
            except Exception as e:
                print(f"  Dashboard navigation note: {e}")

            auth_result = {
                "status": "success",
                "cookie_name": idx_cookie["name"],
                "cookie": idx_cookie["value"],
                "domain": idx_cookie["domain"],
                "user_agent": self.VICTIM_UA,
                "url": page.url,
            }

            return BrowserSession(pw, browser, context, page, auth_result)

        except AuthenticationError:
            raise
        except Exception as e:
            print(f"  Authentication failed: {e}")
            try:
                page.screenshot(path="/tmp/itp-auth-failure.png")
                print("     Screenshot saved to /tmp/itp-auth-failure.png")
            except Exception:
                pass
            video_path = None
            try:
                if page.video:
                    video_path = page.video.path()
            except Exception:
                pass
            context.close()
            browser.close()
            pw.stop()
            raise AuthenticationError(
                str(e),
                video_path=str(video_path) if video_path else None,
            )

    def _build_terminal_html(self, cookie_name: str, cookie_value: str,
                             domain: str) -> str:
        """Build an HTML page that animates the attacker injecting a stolen cookie.

        Renders a terminal-style UI with typed-out commands showing the cookie
        being pasted into the browser's cookie jar. Designed to be visually
        compelling in demo recordings.
        """
        # Truncate cookie for display (full value is too long)
        display_cookie = cookie_value[:40] + "..." + cookie_value[-12:]
        import html as html_mod
        safe_cookie = html_mod.escape(display_cookie)
        safe_domain = html_mod.escape(domain)
        safe_name = html_mod.escape(cookie_name)
        safe_full_cookie = html_mod.escape(cookie_value[:60]) + "..."

        return f'''<!DOCTYPE html>
<html><head><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0a; color: #00ff41; font-family: 'Courier New', monospace;
       font-size: 15px; padding: 30px 40px; line-height: 1.7; }}
.prompt {{ color: #ff3333; }}
.cmd {{ color: #00ff41; }}
.comment {{ color: #666; }}
.output {{ color: #ccc; }}
.success {{ color: #00ff41; font-weight: bold; }}
.warn {{ color: #ffaa00; }}
.cookie-val {{ color: #00ccff; word-break: break-all; }}
.cursor {{ display: inline-block; width: 8px; height: 16px; background: #00ff41;
           animation: blink 0.7s step-end infinite; vertical-align: text-bottom; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.line {{ opacity: 0; white-space: pre-wrap; }}
.line.visible {{ opacity: 1; }}
.header {{ color: #ff3333; font-size: 13px; margin-bottom: 20px; border-bottom: 1px solid #333;
           padding-bottom: 10px; }}
.badge {{ display: inline-block; background: #ff3333; color: #fff; padding: 2px 8px;
          border-radius: 3px; font-size: 11px; margin-left: 10px; }}
</style></head><body>
<div class="header">
  ATTACKER WORKSTATION<span class="badge">SESSION HIJACK</span>
  <span style="float:right; color:#666">Firefox 121.0 / Windows 10 / EU-WEST-1</span>
</div>
<div id="terminal">
<div class="line" data-delay="300"><span class="comment"># Stolen session cookie received from malware C2 callback</span></div>
<div class="line" data-delay="800"><span class="comment"># Target: {safe_domain}</span></div>
<div class="line" data-delay="1400"><span class="prompt">attacker@eu-west-1:~$ </span><span class="cmd">echo $STOLEN_COOKIE</span></div>
<div class="line" data-delay="2200"><span class="cookie-val">{safe_cookie}</span></div>
<div class="line" data-delay="3200">&nbsp;</div>
<div class="line" data-delay="3400"><span class="comment"># Injecting cookie into browser storage...</span></div>
<div class="line" data-delay="4000"><span class="prompt">attacker@eu-west-1:~$ </span><span class="cmd">document.cookie = "{safe_name}={safe_full_cookie}; domain={safe_domain}; path=/; secure"</span></div>
<div class="line" data-delay="5200"><span class="success">✓ Cookie injected successfully</span></div>
<div class="line" data-delay="5800">&nbsp;</div>
<div class="line" data-delay="6000"><span class="comment"># Navigating to target — no credentials needed</span></div>
<div class="line" data-delay="6600"><span class="prompt">attacker@eu-west-1:~$ </span><span class="cmd">open https://{safe_domain}/app/UserHome</span></div>
<div class="line" data-delay="7400"><span class="warn">⏳ Redirecting to Okta dashboard...</span></div>
</div>
<script>
const lines = document.querySelectorAll('.line');
lines.forEach(line => {{
  const delay = parseInt(line.dataset.delay) || 0;
  setTimeout(() => line.classList.add('visible'), delay);
}});
</script>
</body></html>'''

    def _build_cookie_inspector_js(self, cookie_name: str, cookie_value: str,
                                    domain: str) -> str:
        """Build JavaScript that renders a DevTools-style cookie inspector overlay.

        Shown after the attacker lands on the Okta dashboard, proving the
        stolen cookie is present in the browser.
        """
        import html as html_mod
        # Show enough of the cookie to be recognizable but not overwhelming
        display_val = cookie_value[:64] + "..." + cookie_value[-16:]
        safe_val = html_mod.escape(display_val).replace("'", "\\'")
        safe_name = html_mod.escape(cookie_name).replace("'", "\\'")
        safe_domain = html_mod.escape(domain).replace("'", "\\'")

        # Return a full HTML page (not JS) — rendered via set_content() after
        # the attacker visits the dashboard. Overlays on Okta's page don't work
        # in Playwright video (Okta's CSS strips styles, iframes/shadow DOM
        # don't render in headless video capture). A separate page gives us full
        # CSS control and tells a clear "attacker opened DevTools" story.
        return f'''<!DOCTYPE html>
<html><head><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#1e1e1e; font-family:'Courier New',monospace; font-size:13px; color:#d4d4d4; }}
.toolbar {{ background:#2d2d2d; padding:8px 16px; display:flex; align-items:center;
            border-bottom:1px solid #404040; font-size:12px; }}
.toolbar .tab {{ background:#1e1e1e; color:#fff; padding:6px 16px; border-radius:4px 4px 0 0;
                margin-right:4px; font-size:11px; }}
.toolbar .tab.active {{ border-bottom:2px solid #3b82f6; }}
.toolbar .tab.dim {{ color:#666; background:transparent; }}
.panel-header {{ background:#252525; padding:8px 16px; display:flex; align-items:center;
                 border-bottom:1px solid #404040; }}
.panel-header .title {{ color:#ff3333; font-weight:bold; margin-right:10px; font-size:13px; }}
.panel-header .path {{ color:#888; margin-right:4px; }}
.panel-header .domain {{ color:#fff; }}
.badge {{ margin-left:auto; background:#ff3333; color:#fff; padding:3px 10px;
          border-radius:3px; font-size:11px; font-weight:bold; letter-spacing:0.5px; }}
.url-bar {{ background:#1a1a1a; padding:6px 16px; color:#888; border-bottom:1px solid #333;
            font-size:11px; }}
.url-bar span {{ color:#00ff41; }}
table {{ width:100%; border-collapse:collapse; margin-top:0; }}
th {{ padding:8px 14px; border-bottom:1px solid #404040; text-align:left;
     color:#888; background:#252525; font-weight:normal; font-size:12px; }}
td {{ padding:8px 14px; color:#777; font-size:12px; }}
tr.stolen {{ background:#1a2332; border-left:3px solid #ff3333; }}
tr.stolen td:first-child {{ color:#ff3333; font-weight:bold; }}
tr.stolen .val {{ color:#00ccff; word-break:break-all; }}
tr.stolen .dm {{ color:#d4d4d4; }}
.ok {{ color:#00ff41; }}
tr:not(.stolen) {{ border-bottom:1px solid #2a2a2a; }}
</style></head><body>
<div class="toolbar">
  <span class="tab dim">Elements</span>
  <span class="tab dim">Console</span>
  <span class="tab dim">Network</span>
  <span class="tab active">Application</span>
  <span class="tab dim">Security</span>
</div>
<div class="panel-header">
  <span class="title">Cookies</span>
  <span class="path">https://</span><span class="domain">{safe_domain}</span>
  <span class="badge">STOLEN SESSION</span>
</div>
<div class="url-bar">Accessed <span>https://{safe_domain}/app/UserHome</span> &mdash; no credentials required</div>
<table>
  <thead><tr>
    <th style="width:90px">Name</th><th>Value</th><th style="width:170px">Domain</th>
    <th style="width:50px">Path</th><th style="width:65px">Secure</th><th style="width:75px">HttpOnly</th>
  </tr></thead>
  <tbody>
    <tr class="stolen">
      <td>{safe_name}</td><td class="val">{safe_val}</td>
      <td class="dm">{safe_domain}</td><td class="dm">/</td>
      <td class="ok">&#10003;</td><td class="ok">&#10003;</td>
    </tr>
    <tr><td>JSESSIONID</td><td>&mdash;</td><td>{safe_domain}</td><td>/</td>
      <td>&#10003;</td><td>&#10003;</td></tr>
    <tr><td>t</td><td>&mdash;</td><td>{safe_domain}</td><td>/</td>
      <td>&#10003;</td><td>&#10007;</td></tr>
    <tr><td>_okta_throttle</td><td>&mdash;</td><td>{safe_domain}</td><td>/</td>
      <td>&#10003;</td><td>&#10007;</td></tr>
  </tbody>
</table>
</body></html>'''

    def open_attacker_session(self, cookie_name: str, cookie_value: str,
                              domain: str,
                              victim_session: "BrowserSession",
                              record_video: Optional[str] = None) -> "BrowserSession":
        """Open a browser as the attacker: inject stolen cookie, navigate to Okta.

        Simulates what a real attacker does — paste the stolen session cookie
        into a browser and navigate to the target site. No credentials needed.
        The attacker lands directly on the dashboard.

        When recording video, shows a terminal animation of the cookie injection
        followed by a DevTools-style cookie inspector overlay on the dashboard.

        Uses the same Playwright instance as the victim session (Playwright
        only allows one sync instance per process).

        Args:
            cookie_name: Name of the stolen cookie (e.g. "idx")
            cookie_value: Value of the stolen cookie
            domain: Cookie domain (e.g. "taskvantage.okta.com")
            victim_session: The victim's BrowserSession (shares Playwright instance)
            record_video: Directory path for video recording

        Returns:
            BrowserSession wrapping the attacker's browser.
        """
        print(f"  Opening attacker browser (cookie injection)...")
        if record_video:
            print(f"  Recording attacker video to: {record_video}")

        # Reuse the victim's Playwright instance — only one allowed per process
        pw = victim_session._pw
        browser = pw.chromium.launch(headless=True)
        context_opts = {"user_agent": self.ATTACKER_UA}
        if record_video:
            os.makedirs(record_video, exist_ok=True)
            context_opts["record_video_dir"] = record_video
            context_opts["record_video_size"] = {"width": 1280, "height": 720}
        context = browser.new_context(**context_opts)

        # Inject the stolen cookie — this is what a real attacker does
        context.add_cookies([{
            "name": cookie_name,
            "value": cookie_value,
            "domain": domain,
            "path": "/",
        }])
        print(f"  Injected stolen {cookie_name} cookie into attacker browser")

        page = context.new_page()
        page.set_default_timeout(30000)

        # Show terminal animation of cookie injection (for video recording)
        if record_video:
            try:
                print(f"  Playing cookie injection terminal animation...")
                terminal_html = self._build_terminal_html(
                    cookie_name, cookie_value, domain
                )
                # Use set_content — data: URLs truncate large HTML payloads
                page.set_content(terminal_html, wait_until="domcontentloaded")
                # Wait for the full animation to play (last line appears at 7.4s)
                time.sleep(9)
            except Exception as e:
                print(f"  Terminal animation note: {e}")

        # Navigate to Okta — should land on dashboard without any login
        try:
            print(f"  Attacker navigating to {self.okta_url}/app/UserHome...")
            page.goto(f"{self.okta_url}/app/UserHome", wait_until="domcontentloaded")
            time.sleep(2)
            current_url = page.url
            print(f"  Attacker landed on: {current_url}")

            # Check if we actually got in (not redirected to login)
            if "/login/" in current_url.lower() or "/signin/" in current_url.lower():
                print(f"  Attacker was redirected to login — cookie may already be invalid")
            else:
                print(f"  Attacker is IN — no credentials needed!")

                # Show cookie inspector as a separate page (for video).
                # Overlays on Okta's page don't render in Playwright video
                # (Okta's CSS strips styles, iframes/shadow DOM not captured).
                # Navigating to a DevTools-style page tells a clear story:
                #   terminal -> dashboard -> "attacker opens DevTools"
                if record_video:
                    try:
                        # Pause on dashboard so viewer sees the attacker is in
                        time.sleep(3)
                        print(f"  Showing cookie inspector (DevTools view)...")
                        inspector_html = self._build_cookie_inspector_js(
                            cookie_name, cookie_value, domain
                        )
                        # Navigate to about:blank first to clear Okta's CSS,
                        # then set_content with our own styles
                        page.goto("about:blank")
                        page.set_content(inspector_html,
                                         wait_until="domcontentloaded")
                        time.sleep(4)  # Let viewer read the cookie details
                    except Exception as e:
                        print(f"  Cookie inspector note: {e}")
        except Exception as e:
            print(f"  Attacker navigation note: {e}")

        auth_result = {
            "status": "success",
            "cookie_name": cookie_name,
            "cookie": cookie_value,
            "domain": domain,
            "user_agent": self.ATTACKER_UA,
            "url": page.url,
            "role": "attacker",
        }

        return BrowserSession(pw, browser, context, page, auth_result, owns_pw=False)


def wait_for_all_terminated(sessions: dict, timeout: int = 120,
                            poll_interval: int = 5) -> Dict:
    """Watch multiple BrowserSessions for session termination.

    Args:
        sessions: Dict mapping label -> BrowserSession (e.g. {"victim": ..., "attacker": ...})
        timeout: Max seconds to wait
        poll_interval: Seconds between reload cycles

    Returns:
        Dict mapping label -> termination result dict
    """
    print(f"\n  Watching {len(sessions)} browsers for session termination "
          f"({timeout}s, every {poll_interval}s)...")

    results = {}
    active = dict(sessions)  # copy — we remove sessions as they terminate
    start = time.time()

    while time.time() - start < timeout and active:
        time.sleep(poll_interval)
        elapsed = int(time.time() - start)

        for label, session in list(active.items()):
            terminated = False
            reason = None
            try:
                session.page.reload(wait_until="domcontentloaded", timeout=15000)
            except Exception as e:
                print(f"  [{elapsed}s] {label}: reload failed — {e}")
                terminated = True
                reason = f"reload_error: {e}"

            if not terminated:
                current_url = session.page.url.lower()
                for pattern in BrowserSession.LOGIN_URL_PATTERNS:
                    if pattern in current_url:
                        terminated = True
                        reason = "login_redirect"
                        break

            if not terminated:
                try:
                    body = session.page.text_content("body", timeout=3000) or ""
                    body_lower = body.lower()
                    for text in BrowserSession.SESSION_EXPIRED_TEXT:
                        if text in body_lower:
                            terminated = True
                            reason = f"page_content: {text}"
                            break
                except Exception:
                    pass

            if terminated:
                print(f"  [{elapsed}s] {label}: SESSION TERMINATED ({reason})")
                time.sleep(3)  # let login page render for video
                results[label] = {
                    "terminated": True,
                    "elapsed": elapsed,
                    "final_url": session.page.url,
                    "reason": reason,
                }
                del active[label]
            else:
                print(f"  [{elapsed}s] {label}: still active")

    # Handle any sessions that didn't terminate before timeout
    for label in active:
        print(f"  Timeout — {label}: session was NOT terminated")
        results[label] = {
            "terminated": False,
            "elapsed": timeout,
            "final_url": active[label].page.url,
            "reason": "timeout",
        }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Authenticate to Okta and capture session cookie"
    )
    parser.add_argument(
        "--org-name",
        default=os.environ.get("OKTA_ORG_NAME"),
        help="Okta organization name"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OKTA_BASE_URL", "okta.com"),
        help="Okta base URL"
    )
    parser.add_argument("--username", required=True, help="Okta username")
    parser.add_argument("--password", help="User password (or use --password-ssm)")
    parser.add_argument("--password-ssm", help="SSM parameter name for password")
    parser.add_argument("--totp-secret", help="TOTP secret (base32)")
    parser.add_argument("--totp-ssm", help="SSM parameter name for TOTP secret")
    parser.add_argument(
        "--aws-profile",
        default=os.environ.get("AWS_PROFILE"),
        help="AWS profile for SSM access"
    )
    parser.add_argument(
        "--aws-region",
        default="us-east-2",
        help="AWS region for SSM (default: us-east-2)"
    )
    parser.add_argument("--output", help="Write result JSON to file")

    args = parser.parse_args()

    if not args.org_name:
        print("Error: --org-name or OKTA_ORG_NAME must be set")
        sys.exit(1)

    # Resolve password
    password = args.password
    if not password and args.password_ssm:
        print(f"Retrieving password from SSM: {args.password_ssm}")
        password = get_ssm_parameter(args.password_ssm, args.aws_region, args.aws_profile)
    if not password:
        print("Error: --password or --password-ssm is required")
        sys.exit(1)

    # Resolve TOTP secret
    totp_secret = args.totp_secret
    if not totp_secret and args.totp_ssm:
        print(f"Retrieving TOTP secret from SSM: {args.totp_ssm}")
        totp_secret = get_ssm_parameter(args.totp_ssm, args.aws_region, args.aws_profile)

    auth = SessionAuthenticator(args.org_name, args.base_url)
    result = auth.authenticate(args.username, password, totp_secret=totp_secret)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResult written to {args.output}")

    if result["status"] == "success":
        print(f"\nCookie: {result['cookie'][:20]}...")
    else:
        print(f"\nError: {result.get('error')}")

    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
