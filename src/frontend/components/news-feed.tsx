"use client";

import type { NewsArticle, Sentiment } from "@/lib/api";

type SentimentFilter = "all" | Sentiment;

const FILTERS: { id: SentimentFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "bullish", label: "Bullish" },
  { id: "bearish", label: "Bearish" },
  { id: "neutral", label: "Neutral" },
];

function sentimentClass(sentiment: Sentiment) {
  if (sentiment === "bullish") return "badge-bullish";
  if (sentiment === "bearish") return "badge-bearish";
  return "badge-neutral";
}

interface NewsFeedProps {
  articles: NewsArticle[];
  filter: SentimentFilter;
  onFilterChange: (filter: SentimentFilter) => void;
  loading?: boolean;
}

export function NewsFeed({
  articles,
  filter,
  onFilterChange,
  loading,
}: NewsFeedProps) {
  return (
    <div className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-100">Macro News</h2>
        <div className="flex gap-1 rounded-lg bg-slate-950/70 p-1">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onFilterChange(item.id)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                filter === item.id
                  ? "bg-slate-700 text-slate-100"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading news...</p>
      ) : !articles.length ? (
        <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-slate-400">
          <p>No summarized news yet.</p>
          <p className="mt-2 text-sm">Run `python main.py --summarize` after scraping.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {articles.map((article) => (
            <article
              key={article.id}
              className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 transition hover:border-slate-700"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${sentimentClass(article.sentiment)}`}
                >
                  {article.sentiment}
                </span>
                <span className="text-xs uppercase tracking-wide text-slate-500">
                  {article.source}
                </span>
                <span className="text-xs text-slate-600">{article.scraped_at}</span>
              </div>
              <h3 className="mb-2 font-medium text-slate-100">{article.title}</h3>
              <p className="whitespace-pre-line text-sm leading-relaxed text-slate-400">
                {article.summary}
              </p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
