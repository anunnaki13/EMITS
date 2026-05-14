# Phase 30 Patterns

## Validation Frontmatter

Current validation files should use:

```yaml
---
phase: 30
requirements:
  - META4-01
nyquist_status: planned
validation_owner: codex
---
```

Archived legacy validation files may use:

```yaml
---
phase: 23
slug: dashboard-drilldown-integration
status: archived
nyquist_status: legacy_exception
nyquist_exception: "Archived before v1.4 metadata standard; validation evidence preserved in this file and phase verification."
metadata_reviewed: "2026-05-14"
---
```

## Archive Index

Archive index rows should include:

- Phase number.
- Phase name.
- Directory link.
- Summary docs count.
- Validation link.
- Verification link.
- Metadata status.

## Templates

Future templates must include:

- Requirement IDs.
- Status.
- Command evidence.
- Residual risks.
- Follow-up owner/path.
- Verification date/actor.

## Health Check

The planning hygiene script should be conservative:

- Check active/current docs and known archive indices.
- Avoid failing on historical `.planning/milestones/v1.3-phases/*` plan text that intentionally references original active paths.
- Fail on missing validation metadata, missing templates, missing v1.3 archive index rows, or stale current next-step text.
