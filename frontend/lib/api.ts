export type DashboardSummary = {
  channels_count: number;
  videos_count: number;
  small_channel_breakouts_count: number;
  avg_outlier_score: number | null;
  top_formats: Array<{ label: string; count: number }>;
  top_niches: Array<{ label: string; count: number }>;
};

export type Outlier = {
  video_id: number;
  youtube_video_id: string;
  title: string;
  channel_title: string | null;
  channel_subscribers: number | null;
  latest_views: number | null;
  views_per_day: number | null;
  outlier_multiplier: number | null;
  outlier_score: number | null;
  is_small_channel_breakout: boolean;
  explanation: string | null;
  url: string;
  classification: null | {
    format_label: string | null;
    niche_label: string | null;
    is_faceless_friendly: boolean | null;
    is_ai_friendly: boolean | null;
    repeatability_score: number | null;
  };
};

export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${getApiBase()}/dashboard/summary`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Не удалось загрузить сводку');
  return response.json();
}

export async function getOutliers(): Promise<Outlier[]> {
  const response = await fetch(`${getApiBase()}/videos/outliers?limit=25`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Не удалось загрузить список аномалий');
  return response.json();
}
