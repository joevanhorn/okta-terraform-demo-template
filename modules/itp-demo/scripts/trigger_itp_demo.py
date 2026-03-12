#!/usr/bin/env python3
"""
trigger_itp_demo.py

Orchestrates ITP (Identity Threat Protection) demo scenarios.
Supports three modes:

  Quick Mode: Sets user risk via admin API. Instant, no infrastructure needed.
              System log shows "Admin reported user risk".

  Real Mode:  Performs actual session hijacking simulation with two-region
              cookie replay. System log shows "Session hijacking detected".

  SSF Mode:   Sends a Shared Signals Framework (SSF) security event via signed
              JWT. System log shows "Security events provider reported risk".

Usage:
    # Quick mode — set user risk directly
    python3 scripts/trigger_itp_demo.py --mode quick \
        --user user@example.com --risk-level HIGH --monitor

    # Quick mode — reset risk
    python3 scripts/trigger_itp_demo.py --mode quick \
        --user user@example.com --risk-level NONE

    # Real mode — two-region session hijacking simulation
    python3 scripts/trigger_itp_demo.py --mode real \
        --user user@example.com --monitor --auto-reset

    # Real mode with specific attacker region
    python3 scripts/trigger_itp_demo.py --mode real \
        --user user@example.com \
        --attacker-region eu-west-1 --monitor

    # SSF mode — security events provider signal
    python3 scripts/trigger_itp_demo.py --mode ssf \
        --user user@example.com --risk-level HIGH --monitor
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, Optional


class ITPDemoTrigger:
    """Orchestrates ITP demo scenarios"""

    def __init__(self, org_name: str, base_url: str, api_token: str):
        self.org_name = org_name
        self.base_url = base_url
        self.api_token = api_token
        self.okta_url = f"https://{org_name}.{base_url}"
        self.api_base = f"{self.okta_url}/api/v1"
        self.headers = {
            "Authorization": f"SSWS {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # --- User Resolution ---

    def resolve_user(self, user_identifier: str) -> Optional[Dict]:
        """Resolve user email/login to user object with ID"""
        print(f"\nResolving user: {user_identifier}...")

        url = f"{self.api_base}/users/{user_identifier}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            user = response.json()
            print(f"  ✅ User: {user.get('profile', {}).get('firstName')} "
                  f"{user.get('profile', {}).get('lastName')} "
                  f"(ID: {user.get('id')})")
            return user
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  ❌ User not found: {user_identifier}")
            else:
                print(f"  ❌ Error resolving user: {e}")
            return None

    # --- Quick Mode ---

    def get_user_risk(self, user_id: str) -> Optional[Dict]:
        """Get current risk level for a user"""
        url = f"{self.api_base}/users/{user_id}/risk"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_msg = e.response.json().get("errorSummary", error_msg)
            except Exception:
                pass
            print(f"  ❌ Error getting user risk: {error_msg}")
            return None

    def set_user_risk(self, user_id: str, risk_level: str) -> Dict:
        """Set user risk level via admin API"""
        url = f"{self.api_base}/users/{user_id}/risk"
        payload = {"riskLevel": risk_level}

        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()

            result = response.json()
            print(f"  ✅ User risk set to: {result.get('riskLevel')}")
            return {"status": "success", "risk": result}

        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_msg = e.response.json().get("errorSummary", error_msg)
            except Exception:
                pass
            print(f"  ❌ Error setting user risk: {error_msg}")
            return {"status": "error", "error": error_msg}

    def run_quick_mode(self, user_email: str, risk_level: str,
                       monitor: bool = False, auto_reset: bool = False,
                       monitor_duration: int = 60) -> bool:
        """
        Quick mode: Set user risk via admin API.

        Args:
            user_email: User email/login
            risk_level: HIGH, MEDIUM, LOW, or NONE
            monitor: Watch system log for events after trigger
            auto_reset: Reset risk to NONE after monitoring
            monitor_duration: How long to monitor (seconds)
        """
        print("=" * 80)
        print("ITP DEMO — QUICK MODE (Admin Risk API)")
        print("=" * 80)

        # Resolve user
        user = self.resolve_user(user_email)
        if not user:
            return False
        user_id = user["id"]

        # Show current risk
        current_risk = self.get_user_risk(user_id)
        if current_risk:
            print(f"  Current risk level: {current_risk.get('riskLevel')}")

        # Set risk level
        print(f"\nSetting risk to {risk_level}...")
        result = self.set_user_risk(user_id, risk_level)
        if result["status"] != "success":
            return False

        # Monitor events if requested
        if monitor and risk_level != "NONE":
            print(f"\nMonitoring for ITP events ({monitor_duration}s)...")
            self._monitor_events(user_email, monitor_duration)

        # Auto-reset if requested (API only accepts HIGH or LOW, not NONE)
        if auto_reset and risk_level == "HIGH":
            print(f"\nResetting risk to LOW...")
            self.set_user_risk(user_id, "LOW")

        print("\n✅ Quick mode complete")
        return True

    # --- Real Mode ---

    def run_real_mode(self, user_email: str, password: Optional[str] = None,
                      totp_secret: Optional[str] = None,
                      password_ssm: Optional[str] = None,
                      totp_ssm: Optional[str] = None,
                      attacker_region: str = "eu-west-1",
                      attacker_lambda: Optional[str] = None,
                      aws_profile: Optional[str] = None,
                      monitor: bool = False, auto_reset: bool = False,
                      monitor_duration: int = 120,
                      record_video: Optional[str] = None,
                      upload_s3: Optional[str] = None) -> bool:
        """
        Real mode: Two-region session hijacking simulation.

        Step 1: Authenticate as user (victim side) — capture IDX cookie
        Step 2: Replay cookie from different region (attacker side)
        Step 3: Monitor for genuine session hijacking detection

        When record_video is set, uses a persistent browser session so the
        video captures the full flow: login -> dashboard -> ULO termination.
        """
        print("=" * 80)
        print("ITP DEMO — REAL MODE (Session Hijacking Simulation)")
        print("=" * 80)
        print(f"  Target user: {user_email}")
        print(f"  Attacker region: {attacker_region}")
        if record_video:
            print(f"  Video recording: {record_video} (persistent browser)")
        print()

        # Import ITP modules
        try:
            from itp.session_authenticator import (
                SessionAuthenticator, AuthenticationError, get_ssm_parameter
            )
            from itp.session_replayer import replay_cookie
        except ImportError as e:
            print(f"Failed to import ITP modules: {e}")
            print("  Ensure scripts/itp/ package exists")
            return False

        # Resolve credentials
        actual_password, actual_totp = self._resolve_credentials(
            password, totp_secret, password_ssm, totp_ssm, aws_profile
        )
        if not actual_password:
            print("Password is required for real mode")
            print("   Use --password, --password-ssm, or ITP_DEMO_PASSWORD env var")
            return False

        # Dispatch: persistent browser (video) vs standard path
        if record_video:
            return self._run_real_mode_persistent(
                user_email, actual_password, actual_totp,
                attacker_region, attacker_lambda, aws_profile,
                monitor, auto_reset, monitor_duration,
                record_video, upload_s3,
            )
        else:
            return self._run_real_mode_standard(
                user_email, actual_password, actual_totp,
                attacker_region, attacker_lambda, aws_profile,
                monitor, auto_reset, monitor_duration,
            )

    def _resolve_credentials(self, password, totp_secret, password_ssm,
                             totp_ssm, aws_profile):
        """Resolve password and TOTP from args or SSM."""
        from itp.session_authenticator import get_ssm_parameter

        actual_password = password
        actual_totp = totp_secret

        if not actual_password and password_ssm:
            print(f"Retrieving password from SSM: {password_ssm}")
            try:
                actual_password = get_ssm_parameter(
                    password_ssm, region=None, profile=aws_profile
                )
            except Exception as e:
                print(f"  Failed to get password from SSM: {e}")

        if not actual_totp and totp_ssm:
            print(f"Retrieving TOTP secret from SSM: {totp_ssm}")
            try:
                actual_totp = get_ssm_parameter(
                    totp_ssm, region=None, profile=aws_profile
                )
            except Exception as e:
                print(f"  Failed to get TOTP secret from SSM: {e}")

        return actual_password, actual_totp

    def _do_cookie_replay(self, cookie_name: str, cookie_value: str,
                          okta_domain: str, attacker_lambda: Optional[str],
                          attacker_region: str,
                          aws_profile: Optional[str]) -> Dict:
        """Execute cookie replay via Lambda or direct."""
        from itp.session_replayer import replay_cookie

        if attacker_lambda:
            return self._invoke_attacker_lambda(
                attacker_lambda, attacker_region,
                cookie_name, cookie_value, okta_domain,
                aws_profile
            )
        else:
            print("  No attacker Lambda configured — replaying from this host")
            print("     (Same IP, different User-Agent. For full geo separation, deploy Lambda)")
            return replay_cookie(cookie_name, cookie_value, okta_domain)

    def _run_real_mode_standard(self, user_email, actual_password, actual_totp,
                                attacker_region, attacker_lambda, aws_profile,
                                monitor, auto_reset, monitor_duration) -> bool:
        """Standard real mode path — browser closes after auth."""
        from itp.session_authenticator import SessionAuthenticator

        # Step 1: Authenticate (victim side)
        print("\n" + "-" * 60)
        print("STEP 1: Victim Authentication")
        print("-" * 60)

        auth = SessionAuthenticator(self.org_name, self.base_url)
        auth_result = auth.authenticate(
            user_email, actual_password, totp_secret=actual_totp,
        )

        if auth_result["status"] != "success":
            print(f"\nAuthentication failed: {auth_result.get('error')}")
            return False

        cookie_name = auth_result["cookie_name"]
        cookie_value = auth_result["cookie"]
        okta_domain = f"{self.org_name}.{self.base_url}"

        print(f"\n  Got {cookie_name} cookie from {auth_result.get('url', 'Okta')}")

        # Brief pause to let Okta register the session
        print("\n  Waiting 3s for session to register...")
        time.sleep(3)

        # Step 2: Replay from attacker context
        print("\n" + "-" * 60)
        print("STEP 2: Attacker Cookie Replay")
        print("-" * 60)

        replay_result = self._do_cookie_replay(
            cookie_name, cookie_value, okta_domain,
            attacker_lambda, attacker_region, aws_profile
        )

        if replay_result["status"] != "success":
            print(f"\nCookie replay failed: {replay_result.get('error')}")
            return False

        print(f"\n  Cookie replayed — HTTP {replay_result.get('http_code')}")
        if replay_result.get("lambda_region"):
            print(f"     From region: {replay_result['lambda_region']}")

        # Step 3: Monitor
        if monitor:
            print("\n" + "-" * 60)
            print("STEP 3: Monitoring for Session Hijacking Detection")
            print("-" * 60)
            print(f"  Waiting for Okta to detect the anomaly ({monitor_duration}s)...")
            self._monitor_events(user_email, monitor_duration)

        # Auto-reset
        if auto_reset:
            print("\nResetting user risk to LOW...")
            user = self.resolve_user(user_email)
            if user:
                self.set_user_risk(user["id"], "LOW")

        print("\nReal mode complete")
        return True

    def _run_real_mode_persistent(self, user_email, actual_password, actual_totp,
                                  attacker_region, attacker_lambda, aws_profile,
                                  monitor, auto_reset, monitor_duration,
                                  record_video, upload_s3) -> bool:
        """Persistent browser path — video captures full demo flow.

        Two browsers record simultaneously:
          - Victim: login -> dashboard -> session terminated by ULO
          - Attacker: stolen cookie injected -> dashboard (no login!) -> kicked out
        """
        from itp.session_authenticator import (
            SessionAuthenticator, AuthenticationError, wait_for_all_terminated,
        )

        # Step 1: Authenticate victim with persistent browser
        print("\n" + "-" * 60)
        print("STEP 1: Victim Authentication (persistent browser)")
        print("-" * 60)

        auth = SessionAuthenticator(self.org_name, self.base_url)
        try:
            victim_session = auth.authenticate_persistent(
                user_email, actual_password, totp_secret=actual_totp,
                record_video=os.path.join(record_video, "victim"),
            )
        except AuthenticationError as e:
            print(f"\nBrowser auth failed: {e}")
            print("  Falling back to standard path (no continuous video)...")
            return self._run_real_mode_standard(
                user_email, actual_password, actual_totp,
                attacker_region, attacker_lambda, aws_profile,
                monitor, auto_reset, monitor_duration,
            )
        except ImportError as e:
            print(f"\nPlaywright not available: {e}")
            print("  Falling back to standard path...")
            return self._run_real_mode_standard(
                user_email, actual_password, actual_totp,
                attacker_region, attacker_lambda, aws_profile,
                monitor, auto_reset, monitor_duration,
            )

        attacker_session = None
        victim_video = None
        attacker_video = None

        try:
            okta_domain = f"{self.org_name}.{self.base_url}"
            print(f"\n  Got {victim_session.cookie_name} cookie "
                  f"from {victim_session.auth_result.get('url', 'Okta')}")

            # Brief pause to let Okta register the session
            print("\n  Waiting 3s for session to register...")
            time.sleep(3)

            # Step 2: Attacker opens browser with stolen cookie
            print("\n" + "-" * 60)
            print("STEP 2: Attacker Uses Stolen Cookie")
            print("-" * 60)

            attacker_session = auth.open_attacker_session(
                cookie_name=victim_session.cookie_name,
                cookie_value=victim_session.cookie,
                domain=victim_session.domain,
                victim_session=victim_session,
                record_video=os.path.join(record_video, "attacker"),
            )

            # Step 3: Lambda replay for geo-separated detection
            print("\n" + "-" * 60)
            print("STEP 3: Geo-Separated Replay (triggers Okta detection)")
            print("-" * 60)

            replay_result = self._do_cookie_replay(
                victim_session.cookie_name, victim_session.cookie, okta_domain,
                attacker_lambda, attacker_region, aws_profile,
            )

            if replay_result["status"] != "success":
                print(f"\nCookie replay failed: {replay_result.get('error')}")
            else:
                print(f"\n  Cookie replayed — HTTP {replay_result.get('http_code')}")
                if replay_result.get("lambda_region"):
                    print(f"     From region: {replay_result['lambda_region']}")

            # Step 4: Watch BOTH browsers for ULO session termination
            print("\n" + "-" * 60)
            print("STEP 4: Watching Both Browsers for Session Termination (ULO)")
            print("-" * 60)

            terminations = wait_for_all_terminated(
                {"victim": victim_session, "attacker": attacker_session},
                timeout=monitor_duration,
                poll_interval=5,
            )

            for label, result in terminations.items():
                if result["terminated"]:
                    print(f"\n  {label}: terminated after {result['elapsed']}s")
                    print(f"     Final URL: {result['final_url']}")
                    print(f"     Reason: {result['reason']}")
                else:
                    print(f"\n  {label}: NOT terminated within {monitor_duration}s")

        finally:
            # Close attacker FIRST (it borrows victim's Playwright instance)
            if attacker_session:
                attacker_video = attacker_session.close()
            # Then close victim (owns the Playwright instance, stops it)
            victim_video = victim_session.close()

        # Upload finalized videos to S3
        if upload_s3:
            if victim_video:
                print("\n  Uploading victim video...")
                self._upload_video_to_s3(victim_video, upload_s3, user_email, aws_profile)
            if attacker_video:
                print("\n  Uploading attacker video...")
                self._upload_video_to_s3(attacker_video, upload_s3, user_email, aws_profile)

        # Optional: API event log summary
        if monitor:
            print("\n" + "-" * 60)
            print("Event Log Summary")
            print("-" * 60)
            self._monitor_events(user_email, 30)

        # Auto-reset
        if auto_reset:
            print("\nResetting user risk to LOW...")
            user = self.resolve_user(user_email)
            if user:
                self.set_user_risk(user["id"], "LOW")

        print("\nReal mode complete")
        return True

    # --- SSF Mode ---

    def run_ssf_mode(self, user_email: str, risk_level: str = "HIGH",
                     ssf_config_ssm: str = None,
                     private_key_ssm: str = None,
                     aws_profile: str = None,
                     monitor: bool = False, auto_reset: bool = False,
                     monitor_duration: int = 60) -> bool:
        """
        SSF mode: Send a security event via Shared Signals Framework.

        Sends a signed Security Event Token (SET) to Okta's security events
        endpoint. System log shows "Security events provider reported risk".

        Requires one-time setup via setup_ssf_provider.py first.
        """
        print("=" * 80)
        print("ITP DEMO — SSF MODE (Security Events Provider Signal)")
        print("=" * 80)
        print(f"  Target user:  {user_email}")
        print(f"  Risk level:   {risk_level}")
        print()

        # Resolve user to validate they exist
        user = self.resolve_user(user_email)
        if not user:
            return False
        user_id = user["id"]

        # Import SSF module
        try:
            from itp.ssf_provider import SSFProvider, get_ssf_config_from_ssm
        except ImportError as e:
            print(f"❌ Failed to import SSF module: {e}")
            print("  Ensure scripts/itp/ssf_provider.py exists")
            return False

        # Load provider config from SSM
        print("\nLoading SSF provider config from SSM...")
        try:
            config, private_key_pem = get_ssf_config_from_ssm(
                ssm_prefix=ssf_config_ssm.rsplit("/", 1)[0],
                profile=aws_profile,
            )
            print(f"  Provider: {config.get('provider_name', config.get('issuer'))}")
            print(f"  Issuer:   {config['issuer']}")
            print(f"  Key ID:   {config['key_id']}")
        except Exception as e:
            print(f"  ❌ Failed to load SSF config from SSM: {e}")
            print("  Run setup_ssf_provider.py first to register a provider.")
            return False

        # Build and send SET
        print(f"\nSending risk signal ({risk_level})...")
        provider = SSFProvider(
            org_name=self.org_name,
            base_url=self.base_url,
            api_token=self.api_token,
            issuer=config["issuer"],
            private_key_pem=private_key_pem,
            key_id=config["key_id"],
        )

        result = provider.send_risk_signal(user_email, risk_level)

        if result["status"] != "success":
            print(f"  ❌ Signal failed: {result.get('error')}")
            print(f"     HTTP {result.get('http_code')}")
            return False

        print(f"  ✅ Signal accepted — HTTP {result.get('http_code')}")
        print(f"     JTI: {result.get('jti')}")

        # Monitor events
        if monitor:
            print(f"\nMonitoring for ITP events ({monitor_duration}s)...")
            print("  Looking for: 'Security events provider reported risk'")
            self._monitor_events(user_email, monitor_duration)

        # Auto-reset
        if auto_reset and risk_level.upper() == "HIGH":
            print("\nResetting risk to LOW via SSF signal...")
            reset_result = provider.send_risk_signal(user_email, "LOW")
            if reset_result["status"] == "success":
                print(f"  ✅ Reset signal accepted — HTTP {reset_result.get('http_code')}")
            else:
                print(f"  ⚠️  Reset signal failed: {reset_result.get('error')}")
                print("     Falling back to admin API reset...")
                self.set_user_risk(user_id, "LOW")

        print("\n✅ SSF mode complete")
        return True

    # --- Real Mode Helpers ---

    def _invoke_attacker_lambda(self, function_name: str, region: str,
                                cookie_name: str, cookie_value: str,
                                okta_domain: str,
                                aws_profile: Optional[str] = None) -> Dict:
        """Invoke the attacker Lambda function in a different region"""
        print(f"  Invoking Lambda: {function_name} in {region}...")

        try:
            import boto3

            session_kwargs = {}
            if aws_profile:
                session_kwargs["profile_name"] = aws_profile
            boto_session = boto3.Session(region_name=region, **session_kwargs)
            lambda_client = boto_session.client("lambda")

            payload = {
                "cookie_name": cookie_name,
                "cookie": cookie_value,
                "okta_domain": okta_domain,
                "user_agent_index": 0,
            }

            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            response_payload = json.loads(response["Payload"].read().decode())

            if response.get("FunctionError"):
                return {"status": "error", "error": f"Lambda error: {response_payload}"}

            return response_payload

        except ImportError:
            return {"status": "error", "error": "boto3 not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _upload_video_to_s3(self, video_path: str, bucket: str,
                              user_email: str,
                              aws_profile: Optional[str] = None):
        """Upload recorded video to S3 and print a presigned URL"""
        print(f"\n  Uploading video to s3://{bucket}/...")
        try:
            import boto3
            import glob as glob_mod

            # video_path may be a file path or a directory
            if os.path.isfile(video_path) and video_path.endswith(".webm"):
                webm_files = [video_path]
            else:
                pattern = os.path.join(video_path, "*.webm")
                webm_files = glob_mod.glob(pattern)
            if not webm_files:
                print(f"  ⚠️  No .webm files found in {video_path}")
                return

            session_kwargs = {}
            if aws_profile:
                session_kwargs["profile_name"] = aws_profile
            boto_session = boto3.Session(**session_kwargs)
            s3_client = boto_session.client("s3")

            for webm_file in webm_files:
                # S3 key: {date}/{user}_{timestamp}.webm
                now = datetime.now()
                date_prefix = now.strftime("%Y-%m-%d")
                user_prefix = user_email.split("@")[0]
                timestamp = now.strftime("%H-%M-%S")
                filename = os.path.basename(webm_file)
                s3_key = f"{date_prefix}/{user_prefix}_{timestamp}_{filename}"

                s3_client.upload_file(webm_file, bucket, s3_key)
                print(f"  ✅ Uploaded: s3://{bucket}/{s3_key}")

                # Generate presigned URL (7 days)
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": s3_key},
                    ExpiresIn=7 * 24 * 3600,
                )
                print(f"  🔗 Presigned URL (7 days): {presigned_url}")

        except ImportError:
            print("  ⚠️  boto3 not installed — skipping S3 upload")
        except Exception as e:
            print(f"  ⚠️  S3 upload failed: {e}")

    def _monitor_events(self, user_email: str, duration: int):
        """Monitor ITP events using the ITPEventMonitor"""
        try:
            from monitor_itp_events import ITPEventMonitor
        except ImportError:
            # Try relative import path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, script_dir)
            from monitor_itp_events import ITPEventMonitor

        monitor = ITPEventMonitor(
            self.org_name,
            self.base_url,
            self.session.headers.get("Authorization", "").replace("SSWS ", "")
        )
        monitor.monitor(duration=duration, user=user_email)


def main():
    parser = argparse.ArgumentParser(
        description="Trigger ITP demo scenarios"
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
    parser.add_argument(
        "--api-token",
        default=os.environ.get("OKTA_API_TOKEN"),
        help="Okta API token"
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["quick", "real", "ssf"],
        default="quick",
        help="Demo mode: quick (admin API), real (cookie replay), or ssf (security events provider)"
    )

    # Common options
    parser.add_argument("--user", required=True, help="Target user email")
    parser.add_argument("--monitor", action="store_true", help="Monitor events after trigger")
    parser.add_argument("--auto-reset", action="store_true", help="Reset risk to NONE after demo")
    parser.add_argument(
        "--monitor-duration",
        type=int,
        default=60,
        help="Event monitoring duration in seconds (default: 60)"
    )

    # Quick mode options
    parser.add_argument(
        "--risk-level",
        choices=["HIGH", "LOW"],
        default="HIGH",
        help="Risk level to set (quick mode, default: HIGH). API only accepts HIGH or LOW."
    )

    # Real mode options
    parser.add_argument("--password", default=os.environ.get("ITP_DEMO_PASSWORD"),
                        help="User password (or use ITP_DEMO_PASSWORD env var)")
    parser.add_argument("--password-ssm", help="SSM parameter name for password")
    parser.add_argument("--totp-secret", default=os.environ.get("ITP_DEMO_TOTP_SECRET"),
                        help="TOTP secret (or use ITP_DEMO_TOTP_SECRET env var)")
    parser.add_argument("--totp-ssm", help="SSM parameter name for TOTP secret")
    parser.add_argument("--attacker-region", default="eu-west-1",
                        help="AWS region for attacker Lambda (default: eu-west-1)")
    parser.add_argument("--attacker-lambda", help="Lambda function name for cookie replay")
    parser.add_argument("--record-video", metavar="DIR",
                        help="Record browser session video to directory (real mode only)")
    parser.add_argument("--upload-s3", metavar="BUCKET",
                        help="Upload recorded video to S3 bucket (real mode, requires --record-video)")
    parser.add_argument("--aws-profile", default=os.environ.get("AWS_PROFILE"),
                        help="AWS profile for SSM and Lambda access")

    # SSF mode options
    parser.add_argument("--ssf-config-ssm",
                        default=None,
                        help="SSM parameter path for SSF provider config (auto-derived from --ssm-prefix if not set)")
    parser.add_argument("--private-key-ssm",
                        default=None,
                        help="SSM parameter path for SSF private key (auto-derived from --ssm-prefix if not set)")

    # SSM prefix for auto-deriving paths
    parser.add_argument("--ssm-prefix",
                        help="SSM prefix to auto-derive --password-ssm, --totp-ssm, --ssf-config-ssm, and --private-key-ssm")

    args = parser.parse_args()

    # Auto-derive SSM paths from prefix
    if args.ssm_prefix:
        if not args.password_ssm:
            args.password_ssm = f"{args.ssm_prefix}/password"
        if not args.totp_ssm:
            args.totp_ssm = f"{args.ssm_prefix}/totp-secret"
        if not args.ssf_config_ssm:
            args.ssf_config_ssm = f"{args.ssm_prefix}/ssf-demo/provider-config"
        if not args.private_key_ssm:
            args.private_key_ssm = f"{args.ssm_prefix}/ssf-demo/private-key"

    if not args.org_name or not args.api_token:
        print("Error: OKTA_ORG_NAME and OKTA_API_TOKEN must be set")
        sys.exit(1)

    trigger = ITPDemoTrigger(args.org_name, args.base_url, args.api_token)

    if args.mode == "quick":
        success = trigger.run_quick_mode(
            user_email=args.user,
            risk_level=args.risk_level,
            monitor=args.monitor,
            auto_reset=args.auto_reset,
            monitor_duration=args.monitor_duration,
        )
    elif args.mode == "real":
        success = trigger.run_real_mode(
            user_email=args.user,
            password=args.password,
            totp_secret=args.totp_secret,
            password_ssm=args.password_ssm,
            totp_ssm=args.totp_ssm,
            attacker_region=args.attacker_region,
            attacker_lambda=args.attacker_lambda,
            aws_profile=args.aws_profile,
            monitor=args.monitor,
            auto_reset=args.auto_reset,
            monitor_duration=args.monitor_duration,
            record_video=args.record_video,
            upload_s3=args.upload_s3,
        )
    elif args.mode == "ssf":
        success = trigger.run_ssf_mode(
            user_email=args.user,
            risk_level=args.risk_level,
            ssf_config_ssm=args.ssf_config_ssm,
            private_key_ssm=args.private_key_ssm,
            aws_profile=args.aws_profile,
            monitor=args.monitor,
            auto_reset=args.auto_reset,
            monitor_duration=args.monitor_duration,
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
