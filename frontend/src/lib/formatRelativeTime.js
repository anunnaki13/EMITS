import { differenceInSeconds, differenceInMinutes, differenceInHours,
         differenceInDays, format } from "date-fns";
import { id } from "date-fns/locale";

export function formatRelativeTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const secs = differenceInSeconds(now, date);
  if (secs < 60) return "baru saja";
  const mins = differenceInMinutes(now, date);
  if (mins < 60) return `${mins} menit yang lalu`;
  const hrs = differenceInHours(now, date);
  if (hrs < 24) return `${hrs} jam yang lalu`;
  if (hrs < 48) return "kemarin";
  const days = differenceInDays(now, date);
  if (days < 7) return `${days} hari yang lalu`;
  return format(date, "dd MMM yyyy", { locale: id });
}
