# Requirements: EMITS — Next Milestone Seeds

v1.1 requirements are complete and archived in:

- [v1.1 Requirements Archive](milestones/v1.1-REQUIREMENTS.md)
- [v1.1 Milestone Audit](v1.1-MILESTONE-AUDIT.md)

## Pending Backlog Seeds

These items are intentionally not planned yet. Promote them into the next milestone only after discussion and prioritization.

### Backup Automation (BACKUP2)

- [ ] **BACKUP2-01**: Application can create scheduled backups without manual button clicks.
- [ ] **BACKUP2-02**: Backup history shows last success, size/count summary, and failure reason.
- [ ] **BACKUP2-03**: Retention policy is configurable and old backups are pruned safely.
- [ ] **BACKUP2-04**: Restore continues to require explicit admin confirmation and validates schema before writing.

### Engineering Cleanup

- [ ] **CLEANUP-01**: Resolve existing React `react-hooks/exhaustive-deps` warnings or document intentional exclusions.
- [ ] **CLEANUP-02**: Make local focused pytest runs load test admin credentials consistently without exposing secrets.
- [ ] **CLEANUP-03**: Normalize repository layout so planning, source, and git root expectations are explicit.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BACKUP2-01..04 | Backlog | Pending |
| CLEANUP-01..03 | Backlog | Pending |
