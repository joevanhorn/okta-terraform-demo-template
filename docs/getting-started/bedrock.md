# Getting Started with Amazon Bedrock

Amazon Bedrock is AWS's managed service for calling foundation models (Claude, Llama, Titan, etc.) over a single API — no GPUs to provision, billed per token. In this repo it's the natural backend for the **AI-assisted** workflows (see [`ai-assisted/`](../../ai-assisted/README.md)): generating Terraform, drafting OIG configs, and summarizing plans without sending data to a third-party SaaS.

This guide takes you from "I have an AWS account" to your first successful model call.

**Time:** ~20 minutes (most of it waiting for model-access approval).

> **The #1 thing that trips people up:** Bedrock models are **off by default**. A brand-new account can authenticate perfectly and still get `AccessDeniedException` until you explicitly **request model access** in the console (Step 2). If you only read one section, read that one.

---

## Prerequisites

- An AWS account with permissions to manage Bedrock (or an admin who can grant them).
- AWS CLI v2 installed and configured (`aws --version` → 2.x).
- A region that offers the models you want — this guide uses **`us-east-1`** (broadest model availability). `us-east-2` and `us-west-2` are also common.
- (Optional) Python 3.11+ with `boto3` if you want to call Bedrock from code.

> **This repo's AWS profiles.** If you're working inside the taskvantage environment, remember there are two profiles — use the right one:
> ```bash
> export AWS_PROFILE=taskvantage   # account 959737396568 — taskvantage infra
> # the `default` profile (357013128720) is the Claude Code host, NOT taskvantage
> ```
> Bedrock is regional and per-account, so enable model access in whichever account + region you'll actually call from.

---

## Step 1: Pick a region

Model availability differs by region. Set it once so every command below inherits it:

```bash
export AWS_REGION=us-east-1
```

Confirm Bedrock is reachable and see what's offered:

```bash
aws bedrock list-foundation-models \
  --query "modelSummaries[?providerName=='Anthropic'].[modelId,modelName]" \
  --output table
```

If this returns a table of Anthropic models, your auth and region are good. (Listing models does **not** mean you can invoke them yet — that's Step 2.)

---

## Step 2: Request model access (the critical step)

Foundation models are opt-in per account **and** per region.

1. Open the **Amazon Bedrock** console in your chosen region.
2. Left nav → **Model access** (under "Bedrock configurations").
3. Click **Modify model access** / **Enable specific models**.
4. Select the Anthropic **Claude** models you want, submit, and accept the EULA.
5. Wait for status to flip to **Access granted**. Anthropic models are usually granted within a minute or two; some providers take longer.

Until a model shows **Access granted**, every `invoke`/`converse` call against it returns `AccessDeniedException` — even with full IAM permissions. This is the single most common "why doesn't Bedrock work" cause.

---

## Step 3: IAM permissions

The identity you call from needs Bedrock runtime permissions. A minimal policy for calling models:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:Converse",
        "bedrock:ConverseStream"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockDiscovery",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels",
        "bedrock:ListInferenceProfiles",
        "bedrock:GetFoundationModelAvailability"
      ],
      "Resource": "*"
    }
  ]
}
```

Tighten `Resource` to specific model / inference-profile ARNs once you know which ones you're using. Managing Bedrock **model access** itself (Step 2) needs additional `bedrock:*ModelAccess*` / marketplace permissions — that's typically an admin task, separate from the runtime policy above.

---

## Step 4: Find the exact model ID

Bedrock model identifiers are **region-specific and versioned**, and most current Claude models are called through a **cross-region inference profile** (IDs prefixed with `us.`, `eu.`, etc.) rather than the bare model ID. Don't guess the string — discover it:

```bash
# Base foundation models
aws bedrock list-foundation-models \
  --query "modelSummaries[?providerName=='Anthropic'].modelId" --output table

# Inference profiles (what you usually pass to Converse for newer Claude models)
aws bedrock list-inference-profiles \
  --query "inferenceProfileSummaries[?contains(inferenceProfileId, 'anthropic')].[inferenceProfileId,inferenceProfileName]" \
  --output table
```

Copy the exact `modelId` or `inferenceProfileId` for the model you enabled — that string is what the calls below expect. Capture it once:

```bash
export MODEL_ID="<paste the id from the command above>"   # e.g. a us.anthropic.claude-* inference profile
```

---

## Step 5: First call — AWS CLI

The **Converse API** is the current, model-agnostic way to call chat models on Bedrock:

```bash
aws bedrock-runtime converse \
  --model-id "$MODEL_ID" \
  --messages '[{"role":"user","content":[{"text":"In one sentence, what is Amazon Bedrock?"}]}]' \
  --inference-config '{"maxTokens":300}' \
  --query 'output.message.content[0].text' --output text
```

A one-sentence answer means everything is wired up: auth ✓, region ✓, model access ✓, IAM ✓.

---

## Step 6: First call — from code

### Option A — boto3 (AWS-native, provider-agnostic)

Best when you want one code path for any Bedrock model:

```python
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

resp = client.converse(
    modelId="<your MODEL_ID>",  # the id/inference-profile from Step 4
    messages=[{"role": "user", "content": [{"text": "Say hello in one short sentence."}]}],
    inferenceConfig={"maxTokens": 300},
)

print(resp["output"]["message"]["content"][0]["text"])
```

### Option B — Anthropic SDK on Bedrock (Claude-specific)

If you're specifically building on Claude and want the Anthropic Messages API surface, use the Anthropic SDK's Bedrock client. Model IDs here carry an **`anthropic.` prefix** and are the first-party names:

```bash
pip install "anthropic[bedrock]"
```

```python
from anthropic import AnthropicBedrock

client = AnthropicBedrock(aws_region="us-east-1")

msg = client.messages.create(
    model="anthropic.claude-opus-4-8",   # or anthropic.claude-sonnet-4-6, anthropic.claude-haiku-4-5
    max_tokens=1024,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)
print(msg.content[0].text)
```

Default to the latest and most capable Claude model (**Opus 4.8**) unless you have a reason to trade down; `claude-sonnet-4-6` is the balanced speed/cost option and `claude-haiku-4-5` is the cheapest/fastest. On Bedrock these are `anthropic.claude-opus-4-8`, `anthropic.claude-sonnet-4-6`, and `anthropic.claude-haiku-4-5`. (Note the two integrations use different ID formats: the AWS-native path in Step 5/Option A uses the discovered `modelId`/inference-profile string; the Anthropic SDK uses the `anthropic.`-prefixed name. Don't mix them — a `us.anthropic.*` id in the Anthropic SDK, or a bare `anthropic.claude-opus-4-8` in boto3, will error.)

---

## Costs

Bedrock is pay-per-token with **no idle cost** — you're billed only for input + output tokens on the models you call. Cheaper models (Haiku) cost a fraction of the flagship (Opus). For experimentation the spend is trivial (fractions of a cent per call), but set an **AWS Budgets** alarm before wiring Bedrock into anything automated so a runaway loop can't surprise you. See the [Amazon Bedrock pricing page](https://aws.amazon.com/bedrock/pricing/) for current per-model rates.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `AccessDeniedException` on invoke, but auth otherwise works | Model access not granted for that model/region | Step 2 — enable the model and wait for **Access granted** |
| `AccessDeniedException: not authorized to perform bedrock:Converse` | IAM policy missing the runtime action | Step 3 — add the Bedrock invoke actions |
| `ValidationException: invalid model identifier` | Wrong/region-mismatched model id, or a base id where an inference profile is required | Step 4 — re-run `list-inference-profiles` in **this** region and use that exact id |
| `ResourceNotFoundException` / model not listed | You're in a region that doesn't offer it | Switch `AWS_REGION` to `us-east-1` (or another supported region) |
| `ThrottlingException` | Per-account request-rate limit | Back off and retry; request a quota increase in Service Quotas if sustained |
| Calls hit the wrong account | Wrong AWS profile | `export AWS_PROFILE=taskvantage` (or the correct profile) — see Prerequisites |

---

## Next steps

- Wire Bedrock into the repo's AI-assisted flows — see [`ai-assisted/`](../../ai-assisted/README.md) and [`ai-assisted/PROVIDER_COMPARISON.md`](../../ai-assisted/PROVIDER_COMPARISON.md).
- Back to the [Getting Started decision guide](README.md) or the [Documentation Hub](../README.md).
