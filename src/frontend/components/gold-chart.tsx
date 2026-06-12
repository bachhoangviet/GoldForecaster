"use client";

import { useEffect, useRef } from "react";
import {
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type Time,
} from "lightweight-charts";

import type { MacroHistoryPoint } from "@/lib/api";

interface GoldChartProps {
  points: MacroHistoryPoint[];
  loading?: boolean;
}

function toChartData(points: MacroHistoryPoint[]): LineData<Time>[] {
  return points
    .filter((point) => point.gold_spot >= 800)
    .map((point) => ({
      time: point.recorded_at.slice(0, 10) as Time,
      value: point.gold_spot,
    }));
}

export function GoldChart({ points, loading }: GoldChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "rgba(51, 65, 85, 0.35)" },
        horzLines: { color: "rgba(51, 65, 85, 0.35)" },
      },
      rightPriceScale: {
        borderColor: "rgba(51, 65, 85, 0.6)",
      },
      timeScale: {
        borderColor: "rgba(51, 65, 85, 0.6)",
      },
      height: 320,
    });

    const series = chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 2,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setData(toChartData(points));
    chartRef.current?.timeScale().fitContent();
  }, [points]);

  if (loading) {
    return (
      <div className="panel flex h-[320px] items-center justify-center text-slate-400">
        Loading chart...
      </div>
    );
  }

  if (!points.length) {
    return (
      <div className="panel flex h-[320px] flex-col items-center justify-center gap-2 text-center text-slate-400">
        <p>Chưa có lịch sử giá vàng.</p>
        <p className="text-sm">Chạy `python main.py --run-scraper --macro-only`</p>
      </div>
    );
  }

  return <div ref={containerRef} className="panel w-full overflow-hidden p-2" />;
}
