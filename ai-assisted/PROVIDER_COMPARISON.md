# AI Provider Comparison Guide

This guide helps you choose the right AI provider for generating Okta Terraform code.

## Quick Decision Matrix

| Factor | Gemini | OpenAI | Claude |
|--------|--------|--------|--------|
| **Best For** | Cost-effective bulk generation | Balanced performance | Complex reasoning tasks |
| **Default Model** | gemini-1.5-pro | gpt-4o | claude-sonnet-4 |
| **Cost** | $$ | $$$ | $$$ |
| **Speed** | Fast | Medium | Medium |
| **Context Window** | 1M tokens | 128K tokens | 200K tokens |
| **Code Quality** | Good | Very Good | Excellent |

## Provider Details

### Google Gemini

**Model:** `gemini-1.5-pro`

**Strengths:**
- Largest context window (1M tokens)
- Cost-effective for large codebases
- Native streaming support
- Good at following patterns from examples

**Weaknesses:**
- Sometimes less precise with complex logic
- May need more explicit instructions

**Best Use Cases:**
- Bulk code generation
- Processing large context files
- Cost-sensitive projects
- Tier 3 (Gemini Gem) integration

**Setup:**
```bash
export GEMINI_API_KEY="your-key"
pip install google-generativeai
```

**Cost Estimate:** ~$0.001-0.002 per 1K tokens

---

### OpenAI GPT-4o

**Model:** `gpt-4o`

**Strengths:**
- Well-balanced performance
- Excellent instruction following
- Consistent output format
- Strong at code generation

**Weaknesses:**
- Higher cost than Gemini
- Smaller context window

**Best Use Cases:**
- General-purpose code generation
- When you need reliable, consistent output
- Complex multi-file generation

**Setup:**
```bash
export OPENAI_API_KEY="your-key"
pip install openai
```

**Cost Estimate:** ~$0.005-0.015 per 1K tokens

---

### Anthropic Claude

**Model:** `claude-sonnet-4`

**Strengths:**
- Excellent reasoning capabilities
- Best at understanding complex requirements
- Very good at code explanation
- Strong safety alignment

**Weaknesses:**
- Higher cost
- May be verbose in explanations

**Best Use Cases:**
- Complex infrastructure design
- When you need explanations with code
- Security-sensitive configurations
- Code review and optimization

**Setup:**
```bash
export ANTHROPIC_API_KEY="your-key"
pip install anthropic
```

**Cost Estimate:** ~$0.003-0.015 per 1K tokens

---

## Which Provider Should I Use?

### Decision Tree

```
Start
  │
  ├─▶ Need largest context window?
  │     └─▶ YES → Gemini (1M tokens)
  │
  ├─▶ Budget is primary concern?
  │     └─▶ YES → Gemini (lowest cost)
  │
  ├─▶ Need complex reasoning/planning?
  │     └─▶ YES → Claude (best reasoning)
  │
  ├─▶ Want balanced performance?
  │     └─▶ YES → OpenAI GPT-4o
  │
  └─▶ Default → OpenAI GPT-4o (good all-around)
```

### By Task Type

| Task | Recommended Provider |
|------|---------------------|
| Simple user/group creation | Gemini |
| OAuth app with entitlements | OpenAI or Claude |
| Full demo environment | OpenAI |
| OIG setup with bundles | Claude |
| Cross-org migration | Claude |
| Bulk operations (100+ resources) | Gemini |
| Infrastructure (VPC, EC2, AD) | OpenAI |

---

## Configuration Options

All providers support these options through the CLI:

```bash
# Specify provider
python generate.py --provider gemini
python generate.py --provider openai
python generate.py --provider anthropic

# Specify model (override default)
python generate.py --provider openai --model gpt-4o-mini
python generate.py --provider anthropic --model claude-opus-4-5-20251101
python generate.py --provider gemini --model gemini-1.5-flash
```

### Available Models

**Gemini:**
- `gemini-1.5-pro` (default) - Best quality
- `gemini-1.5-flash` - Faster, lower cost
- `gemini-1.5-pro-002` - Latest version

**OpenAI:**
- `gpt-4o` (default) - Best quality
- `gpt-4o-mini` - Faster, lower cost
- `gpt-4-turbo` - Previous generation

**Claude:**
- `claude-sonnet-4-20250514` (default) - Best balance
- `claude-opus-4-5-20251101` - Most capable
- `claude-3-5-haiku-20241022` - Fastest

---

## Troubleshooting by Provider

### Gemini Issues

**"API key not valid"**
```bash
# Verify key is set
echo $GEMINI_API_KEY

# Test with curl
curl -H "x-goog-api-key: $GEMINI_API_KEY" \
  "https://generativelanguage.googleapis.com/v1/models"
```

**Rate limiting**
- Free tier: 60 requests/minute
- Paid tier: Higher limits
- Solution: Add delays between requests

### OpenAI Issues

**"insufficient_quota"**
- Check billing at platform.openai.com
- Verify payment method is active

**"context_length_exceeded"**
- Reduce context file size
- Use `gpt-4o` (128K) instead of older models (8K)

### Claude Issues

**"overloaded_error"**
- Retry after a few seconds
- Claude has occasional capacity issues

**"invalid_api_key"**
- Ensure key starts with `sk-ant-`
- Verify at console.anthropic.com

---

## Cost Optimization Tips

1. **Start with Gemini** for prototyping (lowest cost)
2. **Use smaller models** for simple tasks (`gpt-4o-mini`, `gemini-flash`)
3. **Reduce context** - Only include relevant examples
4. **Cache responses** - Don't regenerate identical requests
5. **Batch operations** - Combine related requests

### Estimated Costs per Task

| Task | Tokens | Gemini | OpenAI | Claude |
|------|--------|--------|--------|--------|
| 5 users + groups | ~2K | $0.002 | $0.01 | $0.006 |
| OAuth app + entitlements | ~4K | $0.004 | $0.02 | $0.012 |
| Full demo (50 resources) | ~15K | $0.015 | $0.075 | $0.045 |
| Cross-org migration | ~8K | $0.008 | $0.04 | $0.024 |

---

## See Also

- [README.md](README.md) - Main AI-assisted guide
- [providers/](providers/) - Provider implementations
- [context/](context/) - Context files for AI
