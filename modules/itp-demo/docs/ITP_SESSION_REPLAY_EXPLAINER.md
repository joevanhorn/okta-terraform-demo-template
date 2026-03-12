# ITP Session Replay Attack Demo — How It Works

A step-by-step explanation of how the ITP automation simulates a real session hijacking attack and triggers Okta Identity Threat Protection.

## What We're Simulating

A real-world session hijacking attack where an attacker steals a user's browser session cookie and replays it from a different location and device. Okta ITP detects the anomaly and automatically terminates all sessions via Universal Logout.

## The Setup (Infrastructure)

| Component | Where | Purpose |
|-----------|-------|---------|
| **Victim browser** | Playwright headless Chrome in GitHub Actions (US IP) | Authenticates and establishes a legitimate session |
| **Attacker Lambda** | AWS Lambda in **eu-west-1 (Ireland)** | Replays the stolen cookie from a different IP/geo/device |
| **Okta ITP** | Entity Risk Policy | Detects anomaly, triggers Universal Logout |

## Step-by-Step Flow

### Step 1 — Victim Authenticates (Playwright Browser)

A headless Chrome browser opens and navigates to the Okta login page. It enters the test user's username, password, and solves TOTP MFA automatically (the TOTP secret is stored in AWS SSM Parameter Store). After successful login, the script captures the **IDX session cookie** from the browser — this is the "stolen" cookie.

The browser stays open (optionally recording video) so we can watch the session get terminated later.

> **Code**: `scripts/itp/session_authenticator.py`

### Step 2 — Cookie Handoff to the "Attacker"

The captured session cookie value and domain are passed to the Lambda function in eu-west-1 via a direct invoke. This simulates an attacker exfiltrating the cookie (e.g., via malware, XSS, or a compromised endpoint).

### Step 3 — Attacker Replays the Cookie (Lambda in Ireland)

The Lambda function makes an HTTP request to the victim's Okta `/app/UserHome` endpoint with:

- The **stolen session cookie** injected into the request
- A **different User-Agent** (e.g., Windows/Firefox instead of the victim's macOS/Chrome)
- An **AWS Ireland IP address**, not the US IP where the victim authenticated

This creates three distinct anomaly signals: different IP, different geolocation, and different browser/OS fingerprint.

> **Code**: `scripts/itp/session_replayer.py` and `modules/itp-demo/lambda/replayer.py`

### Step 4 — Okta ITP Detects the Anomaly

Okta's ML model sees the same session cookie being used from:

- A **different IP address** (US vs. Ireland)
- A **different geolocation**
- A **different browser/OS fingerprint**

Okta flags this as **session hijacking** and raises a `user.risk.detect` event with high risk.

### Step 5 — Entity Risk Policy Fires

The Entity Risk Policy evaluates the risk signal and matches the configured rule:

1. `policy.entity_risk.evaluate` — policy rule matched
2. `policy.entity_risk.action` — schedules **TERMINATE_ALL_SESSIONS**

### Step 6 — Universal Logout

Okta revokes all active sessions for the user and issues Universal Logout. Both the legitimate victim session AND the attacker session are killed.

If video recording is enabled, you can see the victim's browser get kicked back to the login page in real time.

> **Code**: `scripts/monitor_itp_events.py` watches the system log as this unfolds

## The Event Chain in System Log

```
user.risk.detect                       → "Session hijacking detected" (from attacker IP)
policy.entity_risk.evaluate            → Policy rule matched
policy.entity_risk.action              → TERMINATE_ALL_SESSIONS scheduled
user.session.end                       → Sessions revoked
user.authentication.universal_logout   → Universal Logout issued
```

## How to Run It

### Via GitHub Actions (Recommended)

1. Go to **Actions > "ITP Demo Trigger"** workflow
2. Select `mode: real`
3. Enter the test user email
4. Optionally enable video recording
5. Click **Run workflow**

The workflow handles everything — authentication, cookie capture, Lambda invoke, and event monitoring.

### Via CLI

```bash
python scripts/trigger_itp_demo.py \
  --mode real \
  --user-email <user@example.com> \
  --environment taskvantage-prod
```

## Why This Is Compelling for Demos

1. **It's a real attack** — not simulated via admin API. Okta's ML is genuinely detecting anomalous session usage.
2. **The geographic separation is visible** — US authentication vs. Ireland replay makes the threat obvious.
3. **End-to-end automated** — one button press, watch the whole chain unfold in ~30 seconds.
4. **Video proof** — record the victim's browser session getting terminated in real time.
5. **System log tells the story** — the monitor shows each event as it fires, making the detection-to-response pipeline clear.

## The Three Demo Modes (Context)

The automation supports three modes. The session replay described above is "Real" mode:

| Mode | What It Does | System Log Shows | When to Use |
|------|-------------|-----------------|-------------|
| **Quick** | Sets user risk via Admin API | "Admin reported user risk" | Testing policy actions quickly, no infrastructure needed |
| **Real** | Actual cookie replay across regions | "Session hijacking detected" | Full demo — most impressive and realistic |
| **SSF** | Sends signed JWT security event via Shared Signals Framework | "Security events provider reported risk" | Showing third-party signal ingestion (e.g., CrowdStrike, Zscaler) |

## Key Files

| File | Purpose |
|------|---------|
| `scripts/trigger_itp_demo.py` | Main orchestrator for all three modes |
| `scripts/itp/session_authenticator.py` | Headless browser auth + cookie capture |
| `scripts/itp/session_replayer.py` | Cookie replay with attacker context |
| `scripts/itp/ssf_provider.py` | SSF signed JWT security events |
| `scripts/monitor_itp_events.py` | Real-time system log event watcher |
| `modules/itp-demo/lambda/replayer.py` | Lambda handler for remote cookie replay |
| `environments/taskvantage-prod/terraform/itp_session_replayer.tf` | Lambda infrastructure (eu-west-1) |
| `docs/ITP_AUTOMATION.md` | Full technical documentation |

## Questions?

Reach out to Joe Van Horn or check the full technical docs in `docs/ITP_AUTOMATION.md`.
