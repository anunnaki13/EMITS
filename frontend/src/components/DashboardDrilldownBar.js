import { Link } from "react-router-dom";
import { ArrowLeft, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { buildDashboardReturnUrl, buildDrilldownChips } from "@/utils/dashboardDrilldown";

const DashboardDrilldownBar = ({ drilldown, onReset, className = "" }) => {
  if (!drilldown?.active) return null;

  const chips = buildDrilldownChips(drilldown);
  const returnUrl = buildDashboardReturnUrl(drilldown);

  return (
    <div className={`rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-4 py-3 ${className}`} data-testid="dashboard-drilldown-bar">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <p className="text-xs font-mono uppercase tracking-wider text-cyan-300">Filter dashboard aktif</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {chips.length > 0 ? (
              chips.map((chip) => (
                <Badge key={chip.key} variant="outline" className="max-w-full border-cyan-500/30 bg-slate-950/40 text-cyan-100">
                  <span className="text-slate-400">{chip.label}:</span>
                  <span className="ml-1 max-w-[220px] truncate">{chip.value}</span>
                </Badge>
              ))
            ) : (
              <Badge variant="outline" className="border-cyan-500/30 bg-slate-950/40 text-cyan-100">
                Dari dashboard
              </Badge>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" size="sm" className="border-cyan-500/30 text-cyan-200 hover:bg-cyan-500/10">
            <Link to={returnUrl} aria-label="Kembali ke dashboard dengan filter yang sama">
              <ArrowLeft className="w-4 h-4" />
              Kembali ke dashboard
            </Link>
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onReset}
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
            aria-label="Reset filter dashboard"
          >
            <RotateCcw className="w-4 h-4" />
            Reset filter dashboard
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DashboardDrilldownBar;

