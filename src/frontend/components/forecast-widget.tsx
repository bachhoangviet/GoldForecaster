"use client";

import { useMemo, useState } from "react";

import type { ForecastHorizon, Horizon, Trend } from "@/lib/api";

const HORIZONS: Horizon[] = ["day", "week", "month", "quarter"];

const HORIZON_LABELS: Record<Horizon, string> = {
  day: "Day",
  week: "Week",
  month: "Month",
  quarter: "Quarter",
};

function trendIcon(trend: Trend) {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  return "→";
}

function trendColor(trend: Trend) {
  if (trend === "up") return "text-emerald-400";
  if (trend === "down") return "text-rose-400";
  return "text-slate-300";
}

interface ForecastWidgetProps {
  horizons: ForecastHorizon[];
  createdAt: string | null;
  loading?: boolean;
}

export function ForecastWidget({
  horizons,
  createdAt,
  loading,
}: ForecastWidgetProps) {
  const [active, setActive] = useState<Horizon>("day");

  const byHorizon = useMemo(() => {
    const map = new Map<Horizon, ForecastHorizon>();
    for (const item of horizons) {
      map.set(item.horizon, item);
    }
    return map;
  }, [horizons]);

  const selected = byHorizon.get(active);

  if (loading) {
    return (
      <div className="panel flex h-full min-h-[320px] items-center justify-center text-slate-400">
        Loading forecast...
      </div>
    );
  }

  if (!horizons.length || !selected) {
    return (
      <div className="panel flex h-full min-h-[320px] flex-col items-center justify-center gap-2 text-center text-slate-400">
        <p>No AI forecast yet.</p>
        <p className="text-sm">Run `python main.py --run-pipeline --skip-scrape`</p>
      </div>
    );
  }

  return (
    <div className="panel flex h-full min-h-[320px] flex-col p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gold-bright">AI Forecast</h2>
          {createdAt && (
            <p className="text-xs text-slate-500">Updated {createdAt}</p>
          )}
        </div>
        <div className="flex gap-1 rounded-lg bg-slate-950/70 p-1">
          {HORIZONS.map((horizon) => (
            <button
              key={horizon}
              type="button"
              onClick={() => setActive(horizon)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                active === horizon
                  ? "bg-amber-500/20 text-amber-300"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {HORIZON_LABELS[horizon]}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col justify-center gap-4">
        <div className="flex items-center gap-3">
          <span className={`text-4xl font-bold ${trendColor(selected.trend)}`}>
            {trendIcon(selected.trend)}
          </span>
          <div>
            <p className="text-sm uppercase tracking-wide text-slate-400">
              {HORIZON_LABELS[selected.horizon]} trend
            </p>
            <p className={`text-2xl font-semibold capitalize ${trendColor(selected.trend)}`}>
              {selected.trend}
            </p>
          </div>
        </div>

        <div>
          <div className="mb-1 flex justify-between text-xs text-slate-400">
            <span>Confidence</span>
            <span>{selected.confidence}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all"
              style={{ width: `${selected.confidence}%` }}
            />
          </div>
        </div>

        <p className="text-sm leading-relaxed text-slate-300">{selected.reasoning}</p>
      </div>
    </div>
  );
}
