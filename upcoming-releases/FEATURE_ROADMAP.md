# Feature Roadmap

This document outlines potential features for the Okta Terraform Demo Template. Features are categorized by priority and complexity.

**Last Updated:** 2026-01-06
**Status:** Living Document

---

## Current Status Summary

### Completed Features
| Feature | Status | Completion Date |
|---------|--------|-----------------|
| OPA Integration | ✅ Complete | 2025-12-14 |
| AD Domain Controller Module | ✅ Complete | 2026-01-05 |
| AI-Assisted Tools (Enhanced) | ✅ Complete | 2026-01-06 |
| SAML/AD Prompt Templates | ✅ Complete | 2026-01-06 |

### In Progress
| Feature | Status | Plan Document |
|---------|--------|---------------|
| SCIM Server Integration | 🟡 Release 1 Complete | [SCIM_SERVER_INTEGRATION_PLAN.md](SCIM_SERVER_INTEGRATION_PLAN.md) |

---

## Proposed Features

### Priority 1: High Value / Near Term

#### 1. SAML Federation Module
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 2-3 days

**Description:**
Create a reusable module for org-to-org SAML federation, enabling hub-and-spoke identity architectures.

**Use Cases:**
- Partner organization federation
- Multi-tenant SaaS with customer IdPs
- M&A scenarios (linking Okta orgs)
- Development org federation with production

**Deliverables:**
- [ ] `modules/saml-federation/` - Reusable Terraform module
- [ ] IdP configuration (upstream org)
- [ ] SP configuration (downstream org)
- [ ] Routing rules automation
- [ ] User attribute mapping templates
- [ ] Documentation and examples
- [ ] AI prompt template

**Technical Approach:**
- Uses `okta_idp_saml` for IdP configuration
- Uses `okta_app_saml` for SP/app configuration
- Routing rules via `okta_policy_rule_idp_discovery`
- Profile mapping via `okta_profile_mapping`

---

#### 2. Lifecycle Management Patterns
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 2-3 days

**Description:**
Pre-built Terraform patterns for common Joiner-Mover-Leaver (JML) scenarios.

**Use Cases:**
- New hire onboarding automation
- Department transfer access updates
- Termination and access revocation
- Contractor lifecycle management

**Deliverables:**
- [ ] `examples/lifecycle/joiner/` - New hire patterns
- [ ] `examples/lifecycle/mover/` - Transfer patterns
- [ ] `examples/lifecycle/leaver/` - Offboarding patterns
- [ ] Group-based access templates
- [ ] App assignment automation
- [ ] Documentation with HR integration patterns
- [ ] AI prompt template

**Technical Approach:**
- Group rules for automatic assignment
- Profile-based app assignments
- Lifecycle hooks integration
- Deprovisioning policies

---

#### 3. App Integration Templates Library
**Status:** ⚪ Proposed
**Complexity:** Low-Medium
**Estimated Effort:** 1-2 days per app

**Description:**
Pre-configured Terraform templates for popular SaaS applications.

**Applications to Include:**
- [ ] Salesforce (SAML + SCIM)
- [ ] ServiceNow (SAML + SCIM)
- [ ] Workday (SAML + Import)
- [ ] Microsoft 365 (OIDC + SCIM)
- [ ] AWS IAM Identity Center (SAML + SCIM)
- [ ] GitHub Enterprise (SAML)
- [ ] Slack Enterprise Grid (SAML + SCIM)
- [ ] Zoom (SAML + SCIM)
- [ ] Box (SAML + SCIM)
- [ ] Atlassian (SAML + SCIM)

**Deliverables:**
- [ ] `examples/app-integrations/` directory structure
- [ ] Per-app Terraform templates
- [ ] Attribute mapping configurations
- [ ] SCIM provisioning setup (where applicable)
- [ ] Documentation with SP-side setup instructions
- [ ] AI prompt: "Create a Salesforce integration"

---

#### 4. Compliance Reporting Tools
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 3-4 days

**Description:**
Generate compliance reports from Terraform state and Okta API data.

**Report Types:**
- Access certification status
- User access inventory
- Application entitlements summary
- Policy configuration audit
- MFA enrollment status
- Admin role assignments
- High-risk access report

**Deliverables:**
- [ ] `scripts/generate_compliance_report.py`
- [ ] Report templates (JSON, CSV, HTML)
- [ ] GitHub workflow for scheduled reports
- [ ] Integration with OIG access reviews
- [ ] Documentation

**Use Cases:**
- SOX compliance audits
- SOC2 evidence collection
- HIPAA access reviews
- Internal security audits

---

### Priority 2: Medium Value / Medium Term

#### 5. Event Hook Templates
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 2-3 days

**Description:**
Pre-built event hook configurations for common integration scenarios.

**Hook Templates:**
- [ ] User creation → SIEM logging
- [ ] Failed login → Security alerting
- [ ] Password change → Audit logging
- [ ] Group membership change → Slack notification
- [ ] App assignment → ServiceNow ticket
- [ ] MFA enrollment → Compliance tracking

**Deliverables:**
- [ ] `examples/event-hooks/` directory
- [ ] Lambda function templates (AWS)
- [ ] Terraform for event hook resources
- [ ] Webhook endpoint examples
- [ ] Testing utilities

---

#### 6. Custom Admin Role Templates
**Status:** ⚪ Proposed
**Complexity:** Low
**Estimated Effort:** 1-2 days

**Description:**
Pre-built custom admin role configurations for common scenarios.

**Role Templates:**
- [ ] Help Desk (password reset, unlock only)
- [ ] App Admin (specific apps only)
- [ ] Group Admin (specific groups only)
- [ ] Audit Viewer (read-only access)
- [ ] Security Admin (policies, MFA)
- [ ] Compliance Officer (reports, reviews)

**Deliverables:**
- [ ] `examples/admin-roles/` directory
- [ ] Terraform templates per role
- [ ] Permission documentation
- [ ] Assignment patterns

---

#### 7. Network Zone Templates
**Status:** ⚪ Proposed
**Complexity:** Low
**Estimated Effort:** 1 day

**Description:**
Pre-configured network zone templates for common scenarios.

**Zone Templates:**
- [ ] Corporate Office IPs
- [ ] VPN Exit Points
- [ ] Cloud Provider CIDRs (AWS, Azure, GCP)
- [ ] Blocked Countries (geo-blocking)
- [ ] Partner Organization Networks
- [ ] Home Office Ranges

**Deliverables:**
- [ ] `examples/network-zones/` directory
- [ ] Dynamic zone configurations
- [ ] IP-based zone configurations
- [ ] Policy integration examples

---

#### 8. MFA Policy Templates
**Status:** ⚪ Proposed
**Complexity:** Low-Medium
**Estimated Effort:** 1-2 days

**Description:**
Pre-built MFA policy configurations for different security requirements.

**Policy Templates:**
- [ ] Standard Enterprise (Okta Verify + SMS)
- [ ] High Security (WebAuthn + Okta Verify)
- [ ] Passwordless (FIDO2 + Okta FastPass)
- [ ] Contractor Access (time-based MFA)
- [ ] Privileged Access (step-up authentication)
- [ ] Remote Work (device trust + MFA)

**Deliverables:**
- [ ] `examples/mfa-policies/` directory
- [ ] Authenticator configurations
- [ ] Policy rule templates
- [ ] Sign-on policy integration

---

### Priority 3: Lower Priority / Long Term

#### 9. Multi-Cloud AD Deployment
**Status:** ⚪ Proposed
**Complexity:** High
**Estimated Effort:** 1-2 weeks

**Description:**
Extend AD module to support Azure and GCP deployments.

**Deliverables:**
- [ ] Azure AD DS integration
- [ ] GCP Active Directory option
- [ ] Multi-cloud orchestration
- [ ] Cross-cloud networking

---

#### 10. Okta Workflows Integration
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 3-4 days

**Description:**
Terraform patterns for Okta Workflows configuration (limited provider support).

**Deliverables:**
- [ ] Workflow connection templates
- [ ] Flow export/import utilities
- [ ] Documentation on limitations
- [ ] API-based workflow management scripts

---

#### 11. Identity Provider Hub
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 3-4 days

**Description:**
Pre-built configurations for common external identity providers.

**IdP Templates:**
- [ ] Azure AD (OIDC)
- [ ] Google Workspace (OIDC)
- [ ] Ping Identity (SAML)
- [ ] OneLogin (SAML)
- [ ] ADFS (SAML)
- [ ] Social IdPs (Google, Microsoft, Apple)

**Deliverables:**
- [ ] `examples/identity-providers/` directory
- [ ] Per-IdP Terraform templates
- [ ] Routing rule configurations
- [ ] JIT provisioning setup
- [ ] Attribute mapping templates

---

#### 12. Demo Environment Snapshots
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 2-3 days

**Description:**
Ability to save and restore complete demo environment configurations.

**Features:**
- [ ] Snapshot creation (state + config)
- [ ] Named snapshot storage
- [ ] Quick restore functionality
- [ ] Snapshot sharing between SEs
- [ ] Version management

---

#### 13. Terraform Drift Automation
**Status:** ⚪ Proposed
**Complexity:** Medium
**Estimated Effort:** 2-3 days

**Description:**
Automated drift detection and reconciliation workflows.

**Features:**
- [ ] Scheduled drift detection
- [ ] Drift reporting (email, Slack)
- [ ] Automatic reconciliation options
- [ ] Change tracking and alerting
- [ ] Integration with existing import workflow

---

#### 14. Cost Estimation Tools
**Status:** ⚪ Proposed
**Complexity:** Low
**Estimated Effort:** 1-2 days

**Description:**
Estimate costs for demo environments before deployment.

**Features:**
- [ ] AWS cost estimation (EC2, EBS, etc.)
- [ ] Okta license impact (user count)
- [ ] Duration-based projections
- [ ] Comparison between configurations

---

#### 15. Demo Cleanup Automation
**Status:** ⚪ Proposed
**Complexity:** Low-Medium
**Estimated Effort:** 1-2 days

**Description:**
Automated cleanup of demo resources with safety checks.

**Features:**
- [ ] Selective resource cleanup
- [ ] Cleanup scheduling
- [ ] Dependency-aware destruction
- [ ] Audit trail generation
- [ ] Confirmation workflows

---

## Feature Request Process

### Submitting a Feature Request

1. **Open an Issue** with the `enhancement` label
2. **Provide Context:**
   - Use case description
   - Expected behavior
   - Technical approach (if known)
   - Priority suggestion

### Feature Evaluation Criteria

Features are evaluated based on:
- **Value:** How many users will benefit?
- **Complexity:** How much effort to implement?
- **Risk:** What could go wrong?
- **Dependencies:** What needs to exist first?
- **Alignment:** Does it fit the template's purpose?

### Feature Lifecycle

```
⚪ Proposed → 🔵 Accepted → 🟡 In Progress → ✅ Complete
                 ↓
              ❌ Rejected (with reason)
```

---

## Integration with Existing Features

### How Features Build on Each Other

```
AD Module (✅) ────────────────────────────────────┐
                                                    │
SAML Federation Module (⚪) ──────────────────────┐ │
                                                  │ │
SCIM Server (🟡) ─────────────────────────────────┤ │
                                                  │ │
App Integration Templates (⚪) ────────────────────┤ │
                                                  ▼ │
                                    Complete Demo  ◄─┘
                                    Environment
```

### Recommended Implementation Order

1. **SCIM Server** (in progress) - Enables provisioning demos
2. **App Integration Templates** - Quick wins, high value
3. **SAML Federation Module** - Builds on recent work
4. **Lifecycle Patterns** - Leverages app templates
5. **Compliance Reporting** - Uses all above data

---

## Notes

### Technical Considerations

- All features should follow existing patterns (modules, examples, docs)
- AI-assisted generation should be considered for each feature
- Documentation is mandatory for all features
- Features should be optional (not break existing functionality)

### Resource Constraints

- Features are implemented based on available time
- Complex features may span multiple sessions
- User feedback drives prioritization

---

## References

- [SCIM Server Plan](SCIM_SERVER_INTEGRATION_PLAN.md)
- [OPA Integration Plan](OPA_INTEGRATION_PLAN.md)
- [Main README](../README.md)
- [Documentation Index](../docs/00-INDEX.md)

---

**Maintained By:** Template Maintainers
**Review Frequency:** Monthly
