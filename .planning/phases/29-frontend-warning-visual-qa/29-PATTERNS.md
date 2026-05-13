# Phase 29 Patterns

## React Fetch Hooks

Use the local pattern already present in `RuntimeHealthPanel.js`:

1. Wrap async fetch functions in `useCallback`.
2. Include `getAuthHeader` and explicit state reads in dependency arrays.
3. Place `useEffect` after callback definitions when the dependency array references those callbacks.
4. Keep event handlers calling the same callback so refresh-after-save behavior stays intact.

For filter-driven CRUD pages, the normalized shape is:

```js
const fetchRows = useCallback(async () => {
  // read filters and auth header here
}, [dateFrom, dateTo, getAuthHeader, search, supplier]);

useEffect(() => {
  fetchRows();
  setCurrentPage(1);
}, [fetchRows]);
```

## Visual Smoke Anchors

Prefer stable anchors that already exist:

- `[data-testid="dashboard-page"]`
- `[data-testid="laporan-page"]`
- `[data-testid="data-quality-page"]`
- Text heading `Dispute Monitor`
- `[data-testid="settings-page"]`
- Text heading `Status Operasional`

## Warning Budget

The warning checker should parse `react-hooks/exhaustive-deps` lines from production build output and compare them with `docs/quality/REACT_HOOK_WARNINGS.md`.

Expected behavior:

- Build failure exits non-zero.
- Undocumented warning exits non-zero.
- Stale register entry exits non-zero.
- No hook warnings and an empty register passes.

## State Copy

Covered pages should keep Indonesian operational copy:

- Loading: "Memuat ..."
- Error: "Gagal ..."
- Empty: "Tidak ada ..."
- Success: action-specific success text such as "berhasil disimpan" or "berhasil diekspor"
- Partial data/caveat: explain sparse or unavailable data without English placeholder copy.
