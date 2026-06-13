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
  published_at: string;
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
    confidence: number | null;
    rationale: string | null;
    model: string | null;
  };
  channel_avg_views?: number;
  channel_median_views?: number;
  ratio_to_avg?: number;
  ratio_to_median?: number;
  percentile_bucket?: string;
};

export type Channel = {
  id: number;
  youtube_channel_id: string;
  title: string | null;
  handle: string | null;
  uploads_playlist_id: string | null;
  subscriber_count: number | null;
  view_count: number | null;
  video_count: number | null;
  country: string | null;
  source: string | null;
  tags: string[] | null;
  last_synced_at: string | null;
};

export type TaskRun = {
  id: number;
  provider_task_id: string | null;
  task_type: string;
  status: string;
  channel_id: number | null;
  started_at: string | null;
  finished_at: string | null;
  params: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string | null;
};

export type ChannelImportResult = {
  total_rows: number;
  imported: number;
  skipped: number;
  errors: Array<Record<string, unknown>>;
  channels: Channel[];
};

export type ScanOptions = {
  limit?: number;
  minViews?: number;
  maxViews?: number;
  minViewsPerDay?: number;
  maxViewsPerDay?: number;
  publishedAfter?: string;
  publishedBefore?: string;
  stopAfterMatches?: number;
  saveSkipped?: boolean;
};

export type SyncResponse = {
  task_run_id: number;
  task_id: string;
  channel_id: number;
  status: string;
  requested_limit?: number;
  scan_options?: Record<string, unknown>;
};

export type SyncAllResponse = {
  queued: number;
  tasks: SyncResponse[];
  requested_limit?: number;
  max_channels?: number;
  scan_options?: Record<string, unknown>;
};

export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    return (
      process.env.NEXT_PUBLIC_API_BROWSER_BASE ||
      process.env.NEXT_PUBLIC_API_BASE ||
      'http://localhost:8001'
    );
  }

  return (
    process.env.API_INTERNAL_BASE ||
    process.env.NEXT_PUBLIC_API_BASE ||
    'http://localhost:8001'
  );
}

async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(input, init);
    return res;
  } catch {
    throw new Error('Не удалось подключиться к API. Проверьте, что backend запущен и адрес API указан правильно.');
  }
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiFetch(`${getApiBase()}/dashboard/summary`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Не удалось загрузить сводку');
  return response.json();
}

export type FormatStats = {
  format_label: string;
  videos: number;
  avg_outlier_score: number | null;
  avg_views: number | null;
};

export type OutlierFilters = {
  minOutlierScore?: number;
  smallChannelBreakout?: boolean;
  formatLabel?: string;
  nicheLabel?: string;
  isFacelessFriendly?: boolean;
  isAiFriendly?: boolean;
  minViews?: number;
  maxViews?: number;
  minViewsPerDay?: number;
  maxViewsPerDay?: number;
  publishedAfter?: string;
  publishedBefore?: string;
  sort?: 'outlier_score' | 'views_per_day' | 'published_at' | 'outlier_multiplier' | 'latest_views';
  limit?: number;
};

export async function getOutliers(filters?: OutlierFilters): Promise<Outlier[]> {
  const params = new URLSearchParams();
  params.set('limit', String(filters?.limit ?? 25));
  if (filters?.minOutlierScore != null) params.set('min_outlier_score', String(filters.minOutlierScore));
  if (filters?.smallChannelBreakout != null) params.set('small_channel_breakout', String(filters.smallChannelBreakout));
  if (filters?.formatLabel) params.set('format_label', filters.formatLabel);
  if (filters?.nicheLabel) params.set('niche_label', filters.nicheLabel);
  if (filters?.isFacelessFriendly != null) params.set('is_faceless_friendly', String(filters.isFacelessFriendly));
  if (filters?.isAiFriendly != null) params.set('is_ai_friendly', String(filters.isAiFriendly));
  if (filters?.minViews != null) params.set('min_views', String(filters.minViews));
  if (filters?.maxViews != null) params.set('max_views', String(filters.maxViews));
  if (filters?.minViewsPerDay != null) params.set('min_views_per_day', String(filters.minViewsPerDay));
  if (filters?.maxViewsPerDay != null) params.set('max_views_per_day', String(filters.maxViewsPerDay));
  if (filters?.publishedAfter) params.set('published_after', filters.publishedAfter);
  if (filters?.publishedBefore) params.set('published_before', filters.publishedBefore);
  if (filters?.sort) params.set('sort', filters.sort);
  const response = await apiFetch(`${getApiBase()}/videos/outliers?${params}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Не удалось загрузить список аномалий');
  return response.json();
}

export async function getChannels(): Promise<Channel[]> {
  const res = await apiFetch(`${getApiBase()}/channels`, { cache: 'no-store' });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось загрузить список каналов');
  }
  return res.json();
}

export async function createChannel(payload: {
  channel_id?: string;
  handle?: string;
  source?: string;
  tags?: string[] | null;
  notes?: string | null;
}): Promise<Channel> {
  const res = await apiFetch(`${getApiBase()}/channels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source: 'manual', tags: null, notes: null, ...payload }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось добавить канал');
  }
  return res.json();
}

export async function importChannelsCsv(file: File): Promise<ChannelImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiFetch(`${getApiBase()}/channels/import-csv`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось импортировать CSV');
  }
  return res.json();
}

function buildSyncParams(opts: ScanOptions): URLSearchParams {
  const params = new URLSearchParams();
  if (opts.limit != null) params.set('limit', String(opts.limit));
  if (opts.minViews != null) params.set('min_views', String(opts.minViews));
  if (opts.maxViews != null) params.set('max_views', String(opts.maxViews));
  if (opts.minViewsPerDay != null) params.set('min_views_per_day', String(opts.minViewsPerDay));
  if (opts.maxViewsPerDay != null) params.set('max_views_per_day', String(opts.maxViewsPerDay));
  if (opts.publishedAfter) params.set('published_after', opts.publishedAfter);
  if (opts.publishedBefore) params.set('published_before', opts.publishedBefore);
  if (opts.stopAfterMatches != null) params.set('stop_after_matches', String(opts.stopAfterMatches));
  if (opts.saveSkipped != null) params.set('save_skipped', String(opts.saveSkipped));
  return params;
}

export async function syncChannel(channelId: number, scanOptions?: ScanOptions): Promise<SyncResponse> {
  const params = buildSyncParams(scanOptions ?? {});
  const qs = params.toString();
  const res = await apiFetch(`${getApiBase()}/channels/${channelId}/sync${qs ? '?' + qs : ''}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось запустить синхронизацию');
  }
  return res.json();
}

export async function syncAllChannels(scanOptions?: ScanOptions, maxChannels?: number): Promise<SyncAllResponse> {
  const params = buildSyncParams(scanOptions ?? {});
  if (maxChannels != null) params.set('max_channels', String(maxChannels));
  const qs = params.toString();
  const res = await apiFetch(`${getApiBase()}/channels/sync-all${qs ? '?' + qs : ''}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось запустить синхронизацию всех каналов');
  }
  return res.json();
}

export async function getTasks(limit?: number): Promise<TaskRun[]> {
  const params = new URLSearchParams();
  if (limit != null) params.set('limit', String(limit));
  const qs = params.toString();
  const res = await apiFetch(`${getApiBase()}/tasks${qs ? '?' + qs : ''}`, { cache: 'no-store' });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(extractDetail(body) ?? 'Не удалось загрузить список задач');
  }
  return res.json();
}

export async function getFormatStats(): Promise<FormatStats[]> {
  const res = await apiFetch(`${getApiBase()}/analytics/formats`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Не удалось загрузить статистику форматов');
  return res.json();
}

export type FormatSummary = {
  format_label: string;
  videos: number;
  avg_outlier_score: number | null;
  avg_views: number | null;
  faceless_count: number;
  ai_friendly_count: number;
};

export type FormatDetail = {
  format_label: string;
  description: string | null;
  is_faceless_friendly: boolean | null;
  is_ai_friendly: boolean | null;
  repeatability_prior: number | null;
  videos_count: number;
  avg_views: number | null;
  median_views: number | null;
  max_views: number | null;
  avg_outlier_score: number | null;
  avg_repeatability: number | null;
  trend: number | null;
  top_channels: Array<{ channel_title: string; videos_count: number }>;
};

export type TrendingFormat = {
  format_label: string;
  video_count: number;
  growth_rate: number;
  avg_views: number | null;
};

export async function getFormats(): Promise<FormatSummary[]> {
  const res = await apiFetch(`${getApiBase()}/analytics/formats`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Не удалось загрузить список форматов');
  return res.json();
}

export async function getTrendingFormats(periodDays = 30): Promise<TrendingFormat[]> {
  const res = await apiFetch(`${getApiBase()}/analytics/formats/trending?period_days=${periodDays}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Не удалось загрузить тренды форматов');
  return res.json();
}

export async function getFormatDetail(label: string, periodDays = 30): Promise<FormatDetail> {
  const res = await apiFetch(`${getApiBase()}/analytics/formats/${encodeURIComponent(label)}?period_days=${periodDays}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Не удалось загрузить детали формата');
  return res.json();
}

export type AIClassificationResult = {
  format_label: string | null;
  niche_label: string | null;
  hook_type: string | null;
  target_audience: string | null;
  is_faceless_friendly: boolean | null;
  is_ai_friendly: boolean | null;
  repeatability_score: number | null;
  adaptation_ideas: string[] | null;
  confidence: number | null;
  rationale: string | null;
};

export async function classifyOutliers(
  minOutlierScore = 0.3,
  limit = 50,
  provider?: string,
  model?: string,
): Promise<AIClassificationResult[]> {
  const params = new URLSearchParams();
  params.set('min_outlier_score', String(minOutlierScore));
  params.set('limit', String(limit));
  if (provider) params.set('provider', provider);
  if (model) params.set('model', model);
  const res = await apiFetch(`${getApiBase()}/videos/classify-outliers?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Не удалось классифицировать аномалии');
  return res.json();
}

export async function classifyVideo(videoId: number): Promise<AIClassificationResult> {
  const res = await apiFetch(`${getApiBase()}/videos/${videoId}/classify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error('Не удалось классифицировать видео');
  return res.json();
}

function extractDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null;
  const obj = body as Record<string, unknown>;
  if (typeof obj.detail === 'string') return obj.detail;
  if (Array.isArray(obj.detail)) {
    return obj.detail.map((d: unknown) => {
      if (d && typeof d === 'object') return (d as Record<string, unknown>).msg ?? '';
      return String(d);
    }).filter(Boolean).join('; ');
  }
  return null;
}
