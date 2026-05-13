---
phase: 06-operational-unblocks
plan: "05"
subsystem: frontend/ai-chat
tags: [frontend, ai-chat-ui, indonesian-localization, sonner, react-markdown]
dependency_graph:
  requires: [06-01, 06-04]
  provides: [ai-chat-ui, indonesian-error-ux]
  affects: [App.js, Layout.js, SmartBlendingPage.js]
tech_stack:
  added: []
  patterns: [useState+useEffect+axios, React.memo, IntersectionObserver, optimistic-UI]
key_files:
  created:
    - pltu-tenayan-full-backup/frontend/src/pages/AIChatPage.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/ConversationSidebar.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/ConversationListItem.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/ConversationPanel.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/ConversationPanelHeader.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/MessageList.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/MessageBubble.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/MessageInputBar.js
    - pltu-tenayan-full-backup/frontend/src/components/ai-chat/EmptyState.js
    - pltu-tenayan-full-backup/frontend/src/lib/formatRelativeTime.js
  modified:
    - pltu-tenayan-full-backup/frontend/src/App.js
    - pltu-tenayan-full-backup/frontend/src/components/Layout.js
    - pltu-tenayan-full-backup/frontend/src/pages/SmartBlendingPage.js
decisions:
  - "handleApiError inlined per-file (not a shared module) — keeps components self-contained; shared helper deferred since only 2 call sites"
  - "AIChatPage height uses h-[calc(100vh-112px)] per UI-SPEC explicit override"
  - "SmartBlendingPage error catch replaced with full 4-class taxonomy (Rule 2 — OPS-02 correctness)"
metrics:
  duration: "~7 minutes"
  completed: "2026-05-11"
  tasks_completed: 2
  files_changed: 13
---

# Phase 6 Plan 05: AI Chat UI Summary

**One-liner:** 8-component AI chat UI wired to 4 Plan-06-04 endpoints, Indonesian sonner toasts (ERR-01..06), and SmartBlendingPage English-toast localized.

## Tasks Completed

| Task | Files | Commit |
|------|-------|--------|
| 06-05-01: 8 components + helper + route + nav | 12 new/modified files | 4d084f3 (inner) |
| 06-05-02: Indonesian error toasts + SmartBlending fix | AIChatPage, ConversationPanel, SmartBlendingPage | 4d084f3 (inner) |

## Component Inventory (UI-SPEC §1–10 coverage)

| Component | File | Key feature |
|-----------|------|------------|
| AIChatPage | pages/AIChatPage.js:1 | Route container; Sheet sidebar on mobile; fetchConversations + handleNewConversation |
| ConversationSidebar | ai-chat/ConversationSidebar.js:1 | w-72 aside, skeleton loading, Percakapan Baru button |
| ConversationListItem | ai-chat/ConversationListItem.js:1 | React.memo, aria-pressed, formatRelativeTime |
| ConversationPanel | ai-chat/ConversationPanel.js:1 | messages state, optimistic send, 503 rollback, lazy-load cursor |
| ConversationPanelHeader | ai-chat/ConversationPanelHeader.js:1 | h-12, MessageSquare icon, truncated title |
| MessageList | ai-chat/MessageList.js:1 | IntersectionObserver sentinel, scroll-pos preservation |
| MessageBubble | ai-chat/MessageBubble.js:1 | React.memo, user/AI variants, ReactMarkdown+remarkGfm |
| MessageInputBar | ai-chat/MessageInputBar.js:1 | auto-grow textarea, Enter/Shift+Enter, 44px touch target |
| EmptyState | ai-chat/EmptyState.js:1 | Belum ada percakapan, Mulai Percakapan CTA |
| formatRelativeTime | lib/formatRelativeTime.js:1 | date-fns id locale, TS-01..06 |

## Indonesian String Coverage

NAV-01, HDR-01, HDR-02, SDB-01, SDB-02, SDB-03, EMP-01, EMP-02, EMP-03, MSG-01, MSG-02, MSG-04, MSG-05, MSG-06, ERR-01, ERR-02, ERR-03, ERR-04, ERR-05, ERR-06, TS-01..06, A11Y-01..07 — all implemented verbatim.

## Build Output

`yarn build` succeeded in 181.95s. No compile errors.

## Grep Gate Results

- `grep -c 'path="/ai-chat"' App.js` → 1 PASS
- `grep -c 'to="/ai-chat"' Layout.js` → 1 PASS
- `grep -c "ai_conversations" src/ -r` → 0 PASS
- `grep -c "AI recommendation generated successfully"` → 0 PASS
- `grep -c "Rekomendasi AI berhasil dibuat!" SmartBlendingPage.js` → 1 PASS
- "Layanan AI tidak tersedia" → 3 matches PASS
- "Tidak terhubung ke server" → 3 matches PASS
- "Sesi habis. Silakan login ulang" → 3 matches PASS
- "Coba lagi" → 4 matches PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] SmartBlendingPage error taxonomy**
- **Found during:** Task 06-05-02
- **Issue:** Original catch block used `error.response?.data?.detail || "Failed to get recommendation"` — surfaces English + raw server errors to UI; violates OPS-02 SC "no raw BadGatewayError surfaced"
- **Fix:** Replaced with full 4-class Indonesian error taxonomy (network/401/503/5xx)
- **Files modified:** SmartBlendingPage.js:72-83
- **Commit:** 4d084f3

**2. [Rule 2 - Missing critical functionality] handleApiError inlined vs shared module**
- **Found during:** Task 06-05-02
- **Issue:** Plan suggested optional `handleApiError.js` shared helper; inlined instead in AIChatPage + ConversationPanel for self-contained components (2 call sites do not justify a shared module)
- **Fix:** Inline per-file — identical 4-class taxonomy in both files
- **Commit:** 4d084f3

## Known Stubs

None. All data flows from live API endpoints per Plan 06-04.

## Threat Surface Scan

No new trust boundaries beyond what is in the plan's threat model. ReactMarkdown used without rehype-raw (T-06-05-01 mitigated). Optimistic rollback on 503 implemented (T-06-05-03 mitigated).

## Self-Check: PASSED

- AIChatPage.js: EXISTS
- components/ai-chat/ (9 files): EXISTS
- lib/formatRelativeTime.js: EXISTS
- App.js route `/ai-chat`: EXISTS
- Layout.js nav `Riwayat Percakapan AI`: EXISTS
- Inner repo commit 4d084f3: EXISTS
- Build: COMPILED SUCCESSFULLY
