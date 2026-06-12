"use client";

import { useCallback, useEffect, useState } from "react";

import { ForecastWidget } from "@/components/forecast-widget";
import { GoldChart } from "@/components/gold-chart";
import { NewsFeed } from "@/components/news-feed";
import {
  fetchForecastsLatest,
  fetchMacroHistory,
  fetchMacroLatest,
  fetchNews,
  type ForecastHorizon,
  type MacroHistoryPoint,
  type MacroLatest,
  type NewsArticle,
  type Sentiment,
} from "@/lib/api";

type SentimentFilter = "all" | Sentiment;
const POLL_MS = 60_000;

export function Dashboard() {
  const [macro, setMacro] = useState<MacroLatest | null>(null);
  const [history, setHistory] = useState<MacroHistoryPoint[]>([]);
  const [forecasts, setForecasts] = useState<ForecastHorizon[]>([]);
  const [forecastCreatedAt, setForecastCreatedAt] = useState<string | null>(null);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [filter, setFilter] = useState<SentimentFilter>("all");
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<string>("");

  const loadData = useCallback(async () => {
    try {
      const [latest, historyRes, forecastRes, newsRes] = await Promise.all([
        fetchMacroLatest(),
        fetchMacroHistory(30),
        fetchForecastsLatest(),
        fetchNews(filter === "all" ? undefined : filter),
      ]);
      setMacro(latest);
      setHistory(historyRes.points);
      setForecasts(forecastRes.horizons);
      setForecastCreatedAt(forecastRes.created_at);
      setArticles(newsRes.articles);
      setLastRefresh(new Date().toLocaleString());
    } catch (error) {
      console.error("Dashboard refresh failed", error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    void loadData();
  }, [loadData]);

  useEffect(() => {
    const timer = setInterval(() => {
      void loadData();
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [loadData]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-amber-500/80">
            Gold Market Intelligence
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-50">
            Gold<span className="text-gold">Forecaster</span>
          </h1>
        </div>
        <div className="text-right text-sm text-slate-400">
          {lastRefresh && <p>Last refresh: {lastRefresh}</p>}
          {macro?.gold_spot != null && (
            <p className="font-mono text-lg text-gold-bright">
              ${macro.gold_spot.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </p>
          )}
        </div>
      </header>

      <section className="mb-6 grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
            Gold Price
          </h2>
          <GoldChart points={history} loading={loading} />
        </div>
        <div>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
            AI Outlook
          </h2>
          <ForecastWidget
            horizons={forecasts}
            createdAt={forecastCreatedAt}
            loading={loading}
          />
        </div>
      </section>

      <section>
        <NewsFeed
          articles={articles}
          filter={filter}
          onFilterChange={setFilter}
          loading={loading}
        />
      </section>
    </div>
  );
}
