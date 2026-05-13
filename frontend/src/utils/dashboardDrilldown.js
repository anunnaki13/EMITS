const DASHBOARD_PARAM_KEYS = [
  "from",
  "period",
  "supplier",
  "mode",
  "status",
  "umpire_status",
  "date_from",
  "date_to"
];

const MODE_LABELS = {
  vessel: "Vessel",
  barge: "Barge/Tongkang",
  trucking: "Trucking",
  biomassa: "Biomassa"
};

const STATUS_LABELS = {
  critical: "Kritis",
  warning: "Peringatan",
  normal: "Normal",
  proposed: "Diajukan",
  in_progress: "Proses",
  completed: "Selesai",
  active: "Aktif"
};

const isMeaningful = (value) => Boolean(value && value !== "all");

export const periodToDateRange = (period) => {
  if (!isMeaningful(period)) return { dateFrom: "", dateTo: "" };

  if (/^\d{4}$/.test(period)) {
    return { dateFrom: `${period}-01-01`, dateTo: `${period}-12-31` };
  }

  if (/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) {
    const [year, month] = period.split("-").map(Number);
    const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return {
      dateFrom: `${year}-${String(month).padStart(2, "0")}-01`,
      dateTo: `${year}-${String(month).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`
    };
  }

  return { dateFrom: "", dateTo: "" };
};

export const periodToYearMonth = (period) => {
  if (!isMeaningful(period)) return { year: null, month: null };
  if (/^\d{4}$/.test(period)) return { year: Number(period), month: null };
  if (/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) {
    const [year, month] = period.split("-").map(Number);
    return { year, month };
  }
  return { year: null, month: null };
};

export const parseDashboardDrilldown = (search = "") => {
  const params = new URLSearchParams(search || "");
  const period = params.get("period") || "";
  const supplier = params.get("supplier") || "";
  const mode = params.get("mode") || "";
  const status = params.get("status") || params.get("umpire_status") || "";
  const explicitDateFrom = params.get("date_from") || "";
  const explicitDateTo = params.get("date_to") || "";
  const periodRange = periodToDateRange(period);
  const dateFrom = explicitDateFrom || periodRange.dateFrom;
  const dateTo = explicitDateTo || periodRange.dateTo;
  const fromDashboard = params.get("from") === "dashboard";
  const hasFilters = [period, supplier, mode, status, explicitDateFrom, explicitDateTo].some(isMeaningful);

  return {
    active: fromDashboard || hasFilters,
    fromDashboard,
    hasFilters,
    period,
    supplier,
    mode,
    status,
    dateFrom,
    dateTo,
    explicitDateFrom,
    explicitDateTo,
    yearMonth: periodToYearMonth(period)
  };
};

export const buildDashboardReturnUrl = (drilldown = {}) => {
  const params = new URLSearchParams();
  if (isMeaningful(drilldown.period)) params.set("period", drilldown.period);
  if (isMeaningful(drilldown.supplier)) params.set("supplier", drilldown.supplier);
  if (isMeaningful(drilldown.mode)) params.set("mode", drilldown.mode);
  const query = params.toString();
  return query ? `/dashboard?${query}` : "/dashboard";
};

export const buildDrilldownChips = (drilldown = {}) => {
  const chips = [];
  if (isMeaningful(drilldown.period)) chips.push({ key: "period", label: "Periode", value: drilldown.period });
  if (isMeaningful(drilldown.supplier)) chips.push({ key: "supplier", label: "Supplier", value: drilldown.supplier });
  if (isMeaningful(drilldown.mode)) chips.push({ key: "mode", label: "Moda", value: MODE_LABELS[drilldown.mode] || drilldown.mode });
  if (isMeaningful(drilldown.status)) chips.push({ key: "status", label: "Status", value: STATUS_LABELS[drilldown.status] || drilldown.status });
  if (!isMeaningful(drilldown.period) && (isMeaningful(drilldown.explicitDateFrom) || isMeaningful(drilldown.explicitDateTo))) {
    const range = [drilldown.explicitDateFrom || "...", drilldown.explicitDateTo || "..."].join(" s/d ");
    chips.push({ key: "date", label: "Tanggal", value: range });
  }
  return chips;
};

export const buildResetPath = (pathname, search = "", extraKeys = []) => {
  const params = new URLSearchParams(search || "");
  [...DASHBOARD_PARAM_KEYS, ...extraKeys].forEach((key) => params.delete(key));
  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
};

export const dashboardEmptyText = (drilldown, fallback = "Tidak ada data") => {
  return drilldown?.active ? "Tidak ada data untuk filter dashboard ini." : fallback;
};

