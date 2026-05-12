# ADR-003: React 19 + React Router 7 + Tailwind + Shadcn/UI Frontend Stack

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-003.

## Context

The EMITS frontend is a React Single-Page Application that serves the operator and admin UIs for vessel/barge/trucking/biomassa/PO Batubara/merit-order entry, COA reconciliation with umpire workflow, dashboard visualizations, AI Intelligence Agent chat, smart-stock entry, smart blending recommendations, and PDF/Excel exports. It is built once (CRA + craco shim, Yarn classic) and served as static assets behind the same VPS that runs the FastAPI backend.

The application is in production at PLTU Tenayan; the i18n layer is Indonesian (`REQ-i18n-indonesian-ui`), the visual style is dark-mode SaaS (`REQ-dark-saas-ui`), and the operator workflow assumes server-side pagination (`REQ-pagination-server-side`) with response shape `{items, total, page, page_size, total_pages}` (ADR-008). The frontend communicates with the backend exclusively over `/api/*` (ADR-006) using the `REACT_APP_BACKEND_URL` build-time env var.

The component library is **Shadcn/UI** (the unstyled-component pattern that vendors Radix primitives directly into the project). The code-base imports 25+ `@radix-ui/react-*` packages — these are not pulled as a single Shadcn dependency but as individual Radix primitive packages, which is how Shadcn ships in production. AUTHFIX-04 carries forward an evaluation of whether `@radix-ui/react-select` (used on the register tab Tabs-content) needs upgrade or replacement; the upstream `ResizeObserver loop` warning is mitigated today by a page-level suppressor.

## Decision

The EMITS frontend is **React 19 + React Router 7 + Tailwind CSS + Shadcn/UI (vendored Radix primitives)**, with the supplementary set listed below. The build pipeline is **Yarn 1.x classic + CRA 5 + craco** (no migration to Vite or Next.js in v1).

Locked dependency set (pinned in `frontend/package.json`):

- **Core framework:** `react ^19.0.0`, `react-dom ^19.0.0`, `react-router-dom ^7.5.1`.
- **Component library (Shadcn/UI on Radix):** `@radix-ui/react-select ^2.2.2`, `@radix-ui/react-tabs ^1.1.9`, `@radix-ui/react-dialog ^1.1.11`, `@radix-ui/react-dropdown-menu ^2.1.12`, `@radix-ui/react-popover ^1.1.11`, `@radix-ui/react-toast ^1.2.11`, `@radix-ui/react-tooltip ^1.2.4`, plus the rest of the `@radix-ui/*` family enumerated in `package.json` (25+ primitive packages).
- **Styling:** `tailwindcss ^3.4.17`, `tailwind-merge ^3.2.0`, `tailwindcss-animate ^1.0.7`, `class-variance-authority ^0.7.1`, `clsx ^2.1.1`.
- **HTTP:** `axios ^1.8.4`.
- **Charts:** `recharts ^3.6.0`.
- **Forms:** `react-hook-form ^7.56.2` + `@hookform/resolvers ^5.0.1` + `zod ^3.24.4`.
- **Client-side export:** `jspdf ^4.0.0` + `jspdf-autotable ^5.0.7` for PDF, `xlsx ^0.18.5` for Excel, `file-saver ^2.0.5` for download trigger.
- **Markdown / icons / misc:** `react-markdown ^10.1.0` + `remark-gfm ^4.0.1` (AI agent responses), `lucide-react ^0.507.0`, `cmdk ^1.1.1`, `sonner ^2.0.3`, `next-themes ^0.4.6`.
- **Build:** `react-scripts 5.0.1` (CRA), `@craco/craco ^7.1.0` (config override), `yarn 1.22.22` (declared via `packageManager` field).

## Consequences

**Positive:**

- Server-side pagination + dark-saas UI are already shipped; the stack carries the visual idiom forward without re-evaluation.
- Shadcn/UI vendoring pattern means upgrade decisions are made per-primitive (e.g., AUTHFIX-04 can target `@radix-ui/react-select` alone) instead of as a monolithic library bump.
- Tailwind + class-variance-authority + clsx is the established styling idiom across all module pages; new module pages slot in without re-deciding.
- Recharts handles the dashboard visualizations including the COA delta charts and merit-order pricing curves; jsPDF + xlsx cover client-side export paths the backend doesn't render server-side.
- `react-hook-form` + `zod` aligns with backend Pydantic validation: the same shape lives on both sides of the wire.

**Negative / accepted tradeoffs:**

- **`@radix-ui/react-select` emits a benign `ResizeObserver loop completed with undelivered notifications` warning** during Tabs-content remount (specifically on the register tab). It is currently mitigated by a page-level suppressor at `frontend/public/index.html` (the `addEventListener('error', ...)` shim). AUTHFIX-04 carries forward the Radix-upgrade-or-replace evaluation; the suppressor is a stable-but-not-final mitigation.
- CRA 5 is in maintenance mode upstream; long-term, a migration to Vite (or Next.js if SSR ever lands) is a v2 conversation. Today the build is stable on `react-scripts 5.0.1` + `@craco/craco 7.1.0`.
- Yarn 1.x classic is also EOL upstream; `package.json`'s `packageManager` field declares `yarn@1.22.22+sha512.…` to make the current behavior reproducible. Migration to Yarn Berry / npm / pnpm is a future-phase decision.
- 25+ Radix primitive packages individually pinned means dependency-update PRs are wider than a single library bump; managed by careful version-range hygiene in `package.json`.

## Alternatives Considered

- **Next.js (with App Router)** — rejected for v1. Single-host CRA build serves fine; SSR is not a requirement for an internal-ops app behind plant authentication; hydration cost would not buy any user-facing benefit.
- **Vue 3 / Svelte / SolidJS** — rejected. Workforce skill match favors React; the operational doc suite, the AI chat module, the register/login flows, and the COA reconciliation flow are all already built in React; switching frameworks would mean rewriting every page.
- **Pure HTML + Alpine.js / HTMX** — rejected. The COA reconciliation umpire-workflow UI, the AI chat module with session memory, and the smart-blending recommendation flow are interactive enough that a real component framework is justified. HTMX would make the AI streaming + multi-step COA dispute UI awkward.
- **Material-UI / Chakra / Ant Design (instead of Shadcn/UI on Radix)** — rejected. Shadcn's vendored primitives let us tailor styling per-component without fighting upstream theme APIs; the dark-saas idiom in `REQ-dark-saas-ui` is easier to deliver atop unstyled Radix primitives than atop a heavily-themed component library.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-003 row (line 88: "Tech stack — frontend (LOCKED, implicit/inherited): React 19 + React Router 7 + Tailwind + Shadcn/UI + Axios + Recharts + jsPDF + xlsx, built via Yarn").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/frontend/package.json:47` — `"react": "^19.0.0"`
  - `pltu-tenayan-full-backup/frontend/package.json:53` — `"react-router-dom": "^7.5.1"`
  - `pltu-tenayan-full-backup/frontend/package.json:24` — `"@radix-ui/react-select": "^2.2.2"` (named because of AUTHFIX-04)
  - `pltu-tenayan-full-backup/frontend/package.json:93` — `"tailwindcss": "^3.4.17"`
  - `pltu-tenayan-full-backup/frontend/package.json:34` — `"axios": "^1.8.4"`
  - `pltu-tenayan-full-backup/frontend/package.json:55` — `"recharts": "^3.6.0"`
  - `pltu-tenayan-full-backup/frontend/package.json:43` — `"jspdf": "^4.0.0"`
  - `pltu-tenayan-full-backup/frontend/package.json:61` — `"xlsx": "^0.18.5"`
  - `pltu-tenayan-full-backup/frontend/package.json:95` — `"packageManager": "yarn@1.22.22+sha512..."`
  - `pltu-tenayan-full-backup/frontend/public/index.html` — page-level `ResizeObserver` suppressor (AUTHFIX-04 mitigation)
- **Related constraints:** none direct; ADR-006 covers the `REACT_APP_BACKEND_URL` resolution path; ADR-008 covers the pagination shape the frontend reads via `response.data.items`.
- **Sibling docs:** `pltu-tenayan-full-backup/docs/audit/LOGIN_BUG_RESOLUTION.md` (Radix-related ResizeObserver lineage), Phase-2 AUTHFIX-04 carry-forward note.
