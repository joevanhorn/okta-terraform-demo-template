# Archived Documentation

> **These docs are superseded.** Everything below has been replaced by the current documentation. See the [Documentation Hub](../README.md) for up-to-date guides.

This folder contains documentation that has been superseded by the new simplified documentation structure.

**These documents are kept for historical reference only and are no longer maintained.**

---

## Why These Were Archived

In November 2025, the repository documentation was simplified to make it less intimidating for users with no GitOps experience. The new structure provides:

- **Shorter, focused guides** instead of long comprehensive documents
- **Clear learning paths** based on user goals
- **Progressive complexity** from local usage to full GitOps
- **Integration with AI assistance** (Gemini Gem)

---

## Archived Documents

### Setup & Getting Started Guides

| Document | Original Location | Replaced By |
|----------|-------------------|-------------|
| QUICKSTART.md | Root | [LOCAL-USAGE.md](../../LOCAL-USAGE.md), [GITHUB-BASIC.md](../../GITHUB-BASIC.md) |
| TEMPLATE_SETUP.md | Root | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) |
| SECRETS_SETUP.md | Root | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) |
| 01-GETTING-STARTED.md | docs/ | [LOCAL-USAGE.md](../../LOCAL-USAGE.md), [GITHUB-BASIC.md](../../GITHUB-BASIC.md) |
| FORKING_GUIDE.md | docs/ | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) |
| ENVIRONMENT_SETUP_EXAMPLE.md | docs/ | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) |

### Workflow & Architecture Guides

| Document | Original Location | Replaced By |
|----------|-------------------|-------------|
| WORKFLOWS.md | docs/ | [03-WORKFLOWS-GUIDE.md](../03-WORKFLOWS-GUIDE.md) |
| GITOPS_WORKFLOW.md | docs/ | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) |
| COMPLETE_SOLUTION.md | docs/ | [docs/PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) |

### Demo Build Guides

| Document | Original Location | Replaced By |
|----------|-------------------|-------------|
| SIMPLE_DEMO_BUILD_GUIDE.md | Root | [DEMO_GUIDE.md](../../DEMO_GUIDE.md) |
| DETAILED_DEMO_BUILD_GUIDE.md | testing/ | [LOCAL-USAGE.md](../../LOCAL-USAGE.md), [DEMO_GUIDE.md](../../DEMO_GUIDE.md) |

### Terraform & Import Guides

| Document | Original Location | Replaced By |
|----------|-------------------|-------------|
| TERRAFORM_RESOURCES.md | docs/ | [TERRAFORM-BASICS.md](../../TERRAFORM-BASICS.md) |
| TERRAFORMER_OIG_FAQ.md | docs/ | [TERRAFORMER.md](../TERRAFORMER.md) |
| OIG_MANUAL_IMPORT.md | docs/ | [TERRAFORMER.md](../TERRAFORMER.md) |
| TESTING.md | docs/ | [testing/README.md](../../testing/README.md) |

---

## New Documentation Structure

**Use these guides instead:**

| Your Goal | New Guide | Time |
|-----------|-----------|------|
| Learn Terraform basics | [LOCAL-USAGE.md](../../LOCAL-USAGE.md) | 15 min |
| Version control with GitHub | [GITHUB-BASIC.md](../../GITHUB-BASIC.md) | 20 min |
| Full GitOps with CI/CD | [GITHUB-GITOPS.md](../../GITHUB-GITOPS.md) | 45 min |
| Build demos | [DEMO_GUIDE.md](../../DEMO_GUIDE.md) | 30-60 min |
| Terraform examples | [TERRAFORM-BASICS.md](../../TERRAFORM-BASICS.md) | Reference |
| Troubleshooting | [TROUBLESHOOTING.md](../../TROUBLESHOOTING.md) | Reference |

**Recommended learning path:**
```
LOCAL-USAGE.md → GITHUB-BASIC.md → GITHUB-GITOPS.md
   (15 min)        (20 min)          (45 min)
```

---

## Can I Still Use These?

The archived documents may still work, but:
- They contain outdated references
- They're not being updated
- They don't integrate with the new learning path
- The new guides are shorter and easier to follow

**We strongly recommend using the new documentation.**

---

## Questions?

If you're looking for something that was in these documents but can't find it in the new structure, please open a GitHub issue.
