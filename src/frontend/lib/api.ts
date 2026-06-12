const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export type Sentiment = "bullish" | "bearish" | "neutral";
export type Trend = "up" | "down" | "sideways";
export type Horizon = "day" | "week" | "month" | "quarter";

export interface MacroLatest {
  gold_spot: number | null;
  dxy: number | null;
  us10y: number | null;
  spdr_holdings: number | null;
  recorded_at: string | null;
}

export interface MacroHistoryPoint {
  recorded_at: string;
  gold_spot: number;
  dxy: number | null;
  us10y: number | null;
}

export interface NewsArticle {
  id: number;
  source: string;
  title: string;
  summary: string;
  sentiment: Sentiment;
  scraped_at: string;
  published_at: string | null;
}

export interface ForecastHorizon {
  horizon: Horizon;
  trend: Trend;
  confidence: number;
  reasoning: string;
  created_at: string;
}

async function apiFetch<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchMacroLatest() {
  return apiFetch<MacroLatest>("/api/macro/latest");
}

export function fetchMacroHistory(days = 30) {
  return apiFetch<{ days: number; points: MacroHistoryPoint[] }>(
    `/api/macro/history?days=${days}`,
  );
}

export function fetchNews(sentiment?: Sentiment) {
  const query = sentiment ? `?sentiment=${sentiment}` : "";
  return apiFetch<{ count: number; articles: NewsArticle[] }>(
    `/api/news${query}`,
  );
}

export function fetchForecastsLatest() {
  return apiFetch<{
    created_at: string | null;
    horizons: ForecastHorizon[];
  }>("/api/forecasts/latest");
}
