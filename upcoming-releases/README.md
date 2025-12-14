# Upcoming Releases

This directory contains release plans and roadmaps for features currently in development.

## Purpose

**Why this directory exists:**
- 📋 Document multi-phase feature releases
- 🎯 Track progress across sessions
- 🤝 Enable collaboration and review
- 📊 Provide visibility into development plans
- 💾 Preserve planning context if sessions end unexpectedly

## Active Release Plans

### SCIM Server Integration
**Status:** 🟡 Phase 1 In Progress
**Document:** [SCIM_SERVER_INTEGRATION_PLAN.md](SCIM_SERVER_INTEGRATION_PLAN.md)

A 4-phase release plan for integrating custom SCIM server infrastructure:
- **Release 1:** Core Infrastructure (MVP) - *In Progress*
- **Release 2:** GitHub Actions Automation - *Planned*
- **Release 3:** AI-Assisted Generation - *Planned*
- **Release 4:** Documentation & Examples - *Planned*

**Estimated Completion:** 2-3 weeks

---

## Recently Completed

### Okta Privileged Access (OPA) Integration
**Status:** ✅ Complete
**Document:** [OPA_INTEGRATION_PLAN.md](OPA_INTEGRATION_PLAN.md)
**PR:** [#26](https://github.com/joevanhorn/okta-terraform-demo-template/pull/26)

Single-release integration of the `okta/oktapam` Terraform provider:
- ✅ Provider configuration (commented, optional)
- ✅ Comprehensive resource examples (~450 lines)
- ✅ Setup documentation (~400 lines)
- ✅ AI-assisted code generation patterns (~410 lines)
- ✅ Documentation updates

**Completed:** 2025-12-14

---

## How to Use This Directory

### For Contributors

**Starting a New Feature:**
1. Create a release plan document: `FEATURE_NAME_PLAN.md`
2. Use the SCIM server plan as a template
3. Define clear phases with deliverables
4. Update this README with your plan

**Updating Progress:**
1. Check off completed items in the plan
2. Update status indicators (⚪ → 🟡 → ✅)
3. Document decisions and blockers
4. Keep the plan current

**Completing a Release:**
1. Mark all phases complete
2. Move plan to `completed-releases/` directory (create if needed)
3. Update this README
4. Archive or delete completed plan

### For Reviewers

**Reviewing a Plan:**
1. Check if phases are reasonable and achievable
2. Verify dependencies are identified
3. Ensure success criteria are clear
4. Provide feedback via PR comments

**Tracking Progress:**
1. Reference the plan document
2. Check status indicators
3. Review completed checkboxes
4. Follow along in PRs

---

## Release Plan Template

When creating a new release plan, include:

### Required Sections
- **Overview** - What is being built and why
- **Release Strategy** - Number of phases, timeline
- **Phase Details** - For each phase:
  - Objectives
  - Deliverables (with checkboxes)
  - Dependencies
  - Success criteria
  - Estimated effort
  - Notes
- **Overall Timeline** - Summary table
- **Current Progress** - What's done, in progress, next
- **Dependencies & Prerequisites** - What's needed
- **Testing Strategy** - How to validate
- **Risk Mitigation** - Known risks and mitigation
- **Success Metrics** - How to measure success

### Optional Sections
- Post-release activities
- Related documents
- Approval & sign-off
- Design decisions
- Open questions
- Future enhancements
- Changelog

---

## Status Indicators

Use these consistent status indicators in your plans:

- ⚪ **Planned** - Not yet started
- 🟡 **In Progress** - Actively working on this
- ✅ **Complete** - Finished and merged
- 🔴 **Blocked** - Waiting on dependency or decision
- ⏸️ **Paused** - Temporarily on hold
- ❌ **Cancelled** - Will not be completed

---

## Best Practices

### Writing Release Plans

**Do:**
- ✅ Break large features into manageable phases
- ✅ Define clear success criteria
- ✅ Identify dependencies early
- ✅ Include testing strategy
- ✅ Update plan as you go
- ✅ Document decisions and rationale

**Don't:**
- ❌ Create phases that are too large
- ❌ Skip testing or validation steps
- ❌ Forget to update status
- ❌ Leave open questions unresolved
- ❌ Over-plan distant phases (they will change)

### Managing Releases

**Keep it Current:**
- Update progress weekly (or after major milestones)
- Check off completed items immediately
- Document blockers as they occur
- Revise estimates based on actual effort

**Communicate:**
- Reference plan in PR descriptions
- Link to specific phases in commits
- Update plan in review feedback
- Celebrate completed phases! 🎉

---

## Completed Releases

Move completed plans to `completed-releases/` directory (create if needed):

```bash
mkdir -p completed-releases
mv FEATURE_NAME_PLAN.md completed-releases/
```

Or delete if no longer needed for reference.

---

## Examples

See **[SCIM_SERVER_INTEGRATION_PLAN.md](SCIM_SERVER_INTEGRATION_PLAN.md)** for a complete example of:
- Multi-phase planning
- Clear deliverables
- Comprehensive testing strategy
- Risk mitigation
- Success metrics

---

## Questions?

- **For plan-specific questions:** Comment on the related PR
- **For general release process:** Update this README
- **For template improvements:** Submit a PR with enhancements

---

**Last Updated:** 2025-12-14
**Maintained By:** Template Maintainers
