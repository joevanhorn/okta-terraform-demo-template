# Prompt Template: Backup and Restore Operations

Use this template when you need help with backup or restore operations for your Okta tenant.

---

## Context Files to Paste First

Before using this prompt, paste these context files into your AI assistant:
1. `context/repository_structure.md`
2. `context/terraform_examples.md`

---

## Choose Your Operation

### Option 1: Create a Backup

**Fill in the details:**

```
ENVIRONMENT NAME:
[e.g., myorg, production, demo-healthcare]

BACKUP TYPE:
[Choose one]
- resource-based (full export - users, groups, apps to files)
- state-based (quick - just capture S3 state version)

SCHEDULE:
[Choose one]
- manual (one-time backup now)
- daily (scheduled at specific time)
- weekly (scheduled on specific day)

ADDITIONAL OPTIONS:
- Commit to git: [yes/no]
- Download state file (state-based only): [yes/no]
- Retention days: [number, e.g., 30, 90]
```

**Example prompt:**
```
Help me set up a backup for my production Okta tenant.

Environment: production
Backup type: resource-based
Schedule: weekly (Sunday 2 AM UTC)
Commit to git: yes
Retention: 90 days

Generate the workflow commands and explain what will be backed up.
```

---

### Option 2: Restore from Backup

**Fill in the details:**

```
ENVIRONMENT NAME:
[e.g., myorg, production, demo-healthcare]

RESTORE TYPE:
[Choose one]
- resource-based (restore from exported files)
- state-based (rollback S3 state version)

SNAPSHOT TO RESTORE:
[Choose one]
- latest
- specific ID: [e.g., 2025-01-15T10-30-00]

RESTORE MODE (state-based only):
[Choose one]
- state-only (just restore state file)
- full-restore (restore state + terraform apply)

RESOURCES TO RESTORE (resource-based only):
[Choose any combination]
- all
- users
- groups
- apps
- oig
- config

DRY RUN FIRST:
[yes/no - ALWAYS yes for safety!]
```

**Example prompt:**
```
I need to restore my demo-healthcare tenant after a bad terraform apply.

Environment: demo-healthcare
Restore type: state-based
Snapshot: latest
Restore mode: state-only
Dry run: yes

Generate the commands and explain what will happen.
```

---

### Option 3: List Available Backups

**Example prompt:**
```
How do I list available backups for my myorg environment?

Show me commands for both:
1. Resource-based snapshots (in git)
2. State-based snapshots (S3 versions)
```

---

### Option 4: Set Up Scheduled Backups

**Example prompt:**
```
I want to set up automated backups for my production tenant.

Strategy:
- Daily state-based backups at 3 AM UTC (for quick rollbacks)
- Weekly resource-based backups on Sunday 2 AM UTC (for full DR)
- Keep 30 daily snapshots, 12 weekly snapshots

Generate the workflow configuration for scheduled backups.
```

---

## Common Scenarios

### Scenario: Quick Rollback After Bad Apply

```
I just applied terraform changes that broke my Okta configuration.
I need to quickly rollback to the state before my last apply.

Environment: myorg

Help me:
1. Find the previous state version
2. Restore to that version (dry-run first)
3. Apply the restore
```

### Scenario: Full Disaster Recovery

```
My staging tenant was accidentally deleted/corrupted.
I have a resource-based backup from last week.

Environment: staging
Snapshot: 2025-01-10T02-00-00

Help me restore:
1. Users first
2. Then groups
3. Then apps
4. Finally OIG resources

Show dry-run commands first.
```

### Scenario: Audit/Compliance Check

```
I need to show what my production tenant looked like on January 1st, 2025
for a compliance audit.

Environment: production
Date: 2025-01-01

Help me:
1. Find the backup from that date
2. Generate a report of what existed
```

---

## Expected Output

The AI should provide:

1. **Commands to run** - GitHub workflow commands or CLI commands
2. **What will happen** - Explanation of the backup/restore process
3. **What gets backed up/restored** - List of resources affected
4. **Safety warnings** - Especially for restore operations
5. **Next steps** - What to do after the operation completes

---

## Post-Operation Checklist

After backup:
- [ ] Verify backup committed to git (if applicable)
- [ ] Check manifest file exists
- [ ] Confirm artifact uploaded (if applicable)

After restore:
- [ ] Run `terraform plan` to verify state
- [ ] Check Okta Admin Console for expected resources
- [ ] Verify critical users/groups/apps exist
- [ ] Test authentication flows

---

## Related Documentation

- Backup/Restore Guide: `backup-restore/README.md`
- Resource-Based Details: `backup-restore/resource-based/README.md`
- State-Based Details: `backup-restore/state-based/README.md`
- AWS Backend Setup: `docs/AWS_BACKEND_SETUP.md`
