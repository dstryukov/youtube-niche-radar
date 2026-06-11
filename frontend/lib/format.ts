export function formatNumber(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('ru-RU', { maximumFractionDigits: decimals });
}

export function formatCompact(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  if (value >= 1_000_000) {
    const n = value / 1_000_000;
    return n.toLocaleString('ru-RU', { maximumFractionDigits: 1 }) + ' млн';
  }
  if (value >= 1_000) {
    const n = value / 1_000;
    return n.toLocaleString('ru-RU', { maximumFractionDigits: 1 }) + ' тыс.';
  }
  return value.toLocaleString('ru-RU');
}

export function formatViewsPerDay(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${formatCompact(value)} просмотров/день`;
}

export function formatSubscribers(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return `${formatCompact(value)} подписчиков`;
}
