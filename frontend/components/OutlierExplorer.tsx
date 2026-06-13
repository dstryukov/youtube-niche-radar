'use client';

import { useState, useCallback, useEffect } from 'react';
import { getOutliers } from '../lib/api';
import type { Outlier, OutlierFilters } from '../lib/api';
import { formatNumber, formatViewsPerDay, formatSubscribers, formatCompact } from '../lib/format';

const DEFAULT_FILTERS: OutlierFilters = {
  limit: 25,
};

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

type SelectFilter = {
  faceless: '' | 'yes' | 'no';
  ai: '' | 'yes' | 'no';
};

type Preset = {
  label: string;
  hint: string;
  apply: () => void;
};

export default function OutlierExplorer() {
  const [data, setData] = useState<Outlier[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [minScore, setMinScore] = useState('');
  const [smallBreakout, setSmallBreakout] = useState(false);
  const [formatLabel, setFormatLabel] = useState('');
  const [nicheLabel, setNicheLabel] = useState('');
  const [faceless, setFaceless] = useState<SelectFilter['faceless']>('');
  const [ai, setAi] = useState<SelectFilter['ai']>('');
  const [sort, setSort] = useState<OutlierFilters['sort']>('outlier_score');

  const [minViews, setMinViews] = useState('');
  const [maxViews, setMaxViews] = useState('');
  const [minViewsPerDay, setMinViewsPerDay] = useState('');
  const [maxViewsPerDay, setMaxViewsPerDay] = useState('');
  const [publishedAfter, setPublishedAfter] = useState('');
  const [publishedBefore, setPublishedBefore] = useState('');

  const fetchData = useCallback(async (filters: OutlierFilters) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await getOutliers(filters);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить аномалии');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(DEFAULT_FILTERS);
  }, [fetchData]);

  const buildFilters = useCallback((): OutlierFilters => {
    const f: OutlierFilters = { limit: 25, sort };
    if (minScore) {
      const n = parseFloat(minScore);
      if (!isNaN(n)) f.minOutlierScore = n;
    }
    if (smallBreakout) f.smallChannelBreakout = true;
    if (formatLabel.trim()) f.formatLabel = formatLabel.trim();
    if (nicheLabel.trim()) f.nicheLabel = nicheLabel.trim();
    if (faceless === 'yes') f.isFacelessFriendly = true;
    if (faceless === 'no') f.isFacelessFriendly = false;
    if (ai === 'yes') f.isAiFriendly = true;
    if (ai === 'no') f.isAiFriendly = false;
    if (minViews) {
      const n = parseInt(minViews, 10);
      if (!isNaN(n)) f.minViews = n;
    }
    if (maxViews) {
      const n = parseInt(maxViews, 10);
      if (!isNaN(n)) f.maxViews = n;
    }
    if (minViewsPerDay) {
      const n = parseFloat(minViewsPerDay);
      if (!isNaN(n)) f.minViewsPerDay = n;
    }
    if (maxViewsPerDay) {
      const n = parseFloat(maxViewsPerDay);
      if (!isNaN(n)) f.maxViewsPerDay = n;
    }
    if (publishedAfter) f.publishedAfter = publishedAfter + 'T00:00:00';
    if (publishedBefore) f.publishedBefore = publishedBefore + 'T23:59:59';
    return f;
  }, [minScore, smallBreakout, formatLabel, nicheLabel, faceless, ai, sort, minViews, maxViews, minViewsPerDay, maxViewsPerDay, publishedAfter, publishedBefore]);

  const validate = (): string | null => {
    if (minViews && maxViews && parseInt(minViews, 10) > parseInt(maxViews, 10)) {
      return 'Минимум просмотров не может быть больше максимума.';
    }
    if (minViewsPerDay && maxViewsPerDay && parseFloat(minViewsPerDay) > parseFloat(maxViewsPerDay)) {
      return 'Минимум просмотров в день не может быть больше максимума.';
    }
    if (publishedAfter && publishedBefore && publishedAfter > publishedBefore) {
      return 'Дата начала не может быть позже даты окончания.';
    }
    if (minScore && isNaN(parseFloat(minScore))) {
      return 'Введите корректное число для минимальной аномальности.';
    }
    return null;
  };

  const handleApply = () => {
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    fetchData(buildFilters());
  };

  const handleReset = () => {
    setMinScore('');
    setSmallBreakout(false);
    setFormatLabel('');
    setNicheLabel('');
    setFaceless('');
    setAi('');
    setSort('outlier_score');
    setMinViews('');
    setMaxViews('');
    setMinViewsPerDay('');
    setMaxViewsPerDay('');
    setPublishedAfter('');
    setPublishedBefore('');
    fetchData(DEFAULT_FILTERS);
  };

  const fillAndApply = (overrides: Partial<OutlierFilters>) => {
    setMinScore(overrides.minOutlierScore != null ? String(overrides.minOutlierScore) : '');
    setSmallBreakout(!!overrides.smallChannelBreakout);
    setMinViews(overrides.minViews != null ? String(overrides.minViews) : '');
    setMaxViews(overrides.maxViews != null ? String(overrides.maxViews) : '');
    setMinViewsPerDay(overrides.minViewsPerDay != null ? String(overrides.minViewsPerDay) : '');
    setMaxViewsPerDay(overrides.maxViewsPerDay != null ? String(overrides.maxViewsPerDay) : '');
    setPublishedAfter(overrides.publishedAfter || '');
    setPublishedBefore(overrides.publishedBefore || '');
    setSort(overrides.sort || 'outlier_score');
    setFormatLabel('');
    setNicheLabel('');
    setFaceless('');
    setAi('');

    const filters = { ...DEFAULT_FILTERS, ...overrides };
    fetchData(filters);
  };

  const presets: Preset[] = [
    {
      label: 'Малые прорывы',
      hint: 'Ищет небольшие видео, которые быстро набирают просмотры и могут быть ранним сигналом ниши.',
      apply: () => fillAndApply({ minViews: 1000, maxViews: 10000, smallChannelBreakout: true, sort: 'views_per_day' }),
    },
    {
      label: 'Средние аномалии',
      hint: 'Хорошо подходит для поиска форматов, которые уже доказали спрос.',
      apply: () => fillAndApply({ minViews: 10000, maxViews: 100000, minOutlierScore: 0.3, sort: 'outlier_score' }),
    },
    {
      label: 'Свежие сигналы',
      hint: 'Показывает свежие ролики с быстрым набором просмотров.',
      apply: () => fillAndApply({ minViewsPerDay: 1000, publishedAfter: daysAgo(30), sort: 'published_at' }),
    },
    {
      label: 'Большие хиты',
      hint: 'Полезно для изучения крупных успешных форматов, но не всегда подходит для малых каналов.',
      apply: () => fillAndApply({ minViews: 100000, sort: 'latest_views' }),
    },
  ];

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  const featureLabel = (value: boolean | null | undefined, ifTrue: string, ifFalse: string): string => {
    if (value === true) return ifTrue;
    if (value === false) return ifFalse;
    return 'Неизвестно';
  };

  const formatViews = (views: number | null | undefined): string => {
    if (views == null) return '—';
    if (views >= 1_000_000) return (views / 1_000_000).toFixed(1).replace('.', ',') + ' млн просмотров';
    if (views >= 1_000) return (views / 1_000).toFixed(1).replace('.', ',') + ' тыс. просмотров';
    return String(views) + ' просмотров';
  };

  return (
    <div className="outlier-explorer">
      <div className="filter-panel">
        <div className="filter-grid filter-grid-wide">
          <div className="filter-item">
            <label className="filter-label">Мин. аномальность</label>
            <input
              className="input"
              type="number"
              step="0.1"
              min="0"
              placeholder="0.0"
              value={minScore}
              onChange={e => setMinScore(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Просмотры от</label>
            <input
              className="input"
              type="number"
              min="0"
              placeholder="0"
              value={minViews}
              onChange={e => setMinViews(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Просмотры до</label>
            <input
              className="input"
              type="number"
              min="0"
              placeholder="∞"
              value={maxViews}
              onChange={e => setMaxViews(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Просмотров/день от</label>
            <input
              className="input"
              type="number"
              min="0"
              step="0.1"
              placeholder="0"
              value={minViewsPerDay}
              onChange={e => setMinViewsPerDay(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Просмотров/день до</label>
            <input
              className="input"
              type="number"
              min="0"
              step="0.1"
              placeholder="∞"
              value={maxViewsPerDay}
              onChange={e => setMaxViewsPerDay(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Опубликовано после</label>
            <input
              className="input"
              type="date"
              value={publishedAfter}
              onChange={e => setPublishedAfter(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Опубликовано до</label>
            <input
              className="input"
              type="date"
              value={publishedBefore}
              onChange={e => setPublishedBefore(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Формат</label>
            <input
              className="input"
              type="text"
              placeholder="Например: образовательный"
              value={formatLabel}
              onChange={e => setFormatLabel(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Ниша</label>
            <input
              className="input"
              type="text"
              placeholder="Например: технологии"
              value={nicheLabel}
              onChange={e => setNicheLabel(e.target.value)}
            />
          </div>
          <div className="filter-item">
            <label className="filter-label">Faceless</label>
            <select className="select" value={faceless} onChange={e => setFaceless(e.target.value as SelectFilter['faceless'])}>
              <option value="">Любые</option>
              <option value="yes">Только faceless</option>
              <option value="no">Только не faceless</option>
            </select>
          </div>
          <div className="filter-item">
            <label className="filter-label">AI-friendly</label>
            <select className="select" value={ai} onChange={e => setAi(e.target.value as SelectFilter['ai'])}>
              <option value="">Любые</option>
              <option value="yes">Только AI-friendly</option>
              <option value="no">Только не AI</option>
            </select>
          </div>
          <div className="filter-item">
            <label className="filter-label">Сортировка</label>
            <select className="select" value={sort} onChange={e => setSort(e.target.value as OutlierFilters['sort'])}>
              <option value="outlier_score">По аномальности</option>
              <option value="views_per_day">По просмотрам/день</option>
              <option value="published_at">По дате публикации</option>
              <option value="outlier_multiplier">По multiplier</option>
              <option value="latest_views">По просмотрам</option>
            </select>
          </div>
          <div className="filter-item">
            <label className="filter-label">&nbsp;</label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={smallBreakout}
                onChange={e => setSmallBreakout(e.target.checked)}
              />
              Только прорывы малых каналов
            </label>
          </div>
          <div className="filter-item filter-actions">
            <label className="filter-label">&nbsp;</label>
            <div className="filter-btn-row">
              <button className="btn btn-primary" onClick={handleApply}>Применить</button>
              <button className="btn btn-secondary" onClick={handleReset}>Сбросить</button>
            </div>
          </div>
        </div>

        <div className="preset-section">
          <label className="filter-label preset-label">Рекомендации по фильтрам</label>
          <div className="preset-buttons">
            {presets.map(p => (
              <button key={p.label} className="btn btn-sm btn-outline preset-btn" onClick={p.apply} title={p.hint}>
                {p.label}
              </button>
            ))}
          </div>
          <p className="preset-hint">
            Эти фильтры работают по уже собранным данным. Чтобы экономить quota, используйте настройки сканирования выше.
          </p>
        </div>
      </div>

      <div className="outlier-results">
        {loading ? (
          <div className="outlier-loading">
            <div className="spinner" />
            <span>Загрузка аномалий…</span>
          </div>
        ) : error ? (
          <div className="empty-state">
            <p className="title">{error}</p>
            <p>Проверьте подключение к серверу</p>
          </div>
        ) : data && data.length > 0 ? (
          <div className="outlier-table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Видео</th>
                  <th>Канал</th>
                  <th>Просмотры</th>
                  <th>Скоринг</th>
                  <th>Формат / Признаки</th>
                  <th>Почему аномалия</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.video_id}>
                    <td>
                      <a className="video-title" href={item.url} target="_blank" rel="noopener noreferrer">{item.title}</a>
                      <span className="sub-row">{item.channel_title ?? '—'} · {formatDate(item.published_at)}</span>
                    </td>
                    <td>
                      <span className="channel-name">{formatSubscribers(item.channel_subscribers)}</span>
                      {item.is_small_channel_breakout && (
                        <span className="sub-row"><span className="badge badge-green">Малый канал</span></span>
                      )}
                    </td>
                    <td>
                      <span className="views-count">{formatViews(item.latest_views)}</span>
                      <span className="sub-row">{formatViewsPerDay(item.views_per_day)}</span>
                    </td>
                    <td>
                      <span className="sub-row">Аномальность: <strong>{item.outlier_multiplier != null ? `x${formatNumber(item.outlier_multiplier, 1)}` : '—'}</strong></span>
                      <span className="sub-row">Score: <strong>{item.outlier_score != null ? formatNumber(item.outlier_score, 2) : '—'}</strong></span>
                    </td>
                    <td>
                      {item.classification ? (
                        <>
                          <span className="badge">{item.classification.format_label ?? 'Формат не указан'}</span>
                          {item.classification.niche_label && (
                            <span className="sub-row">{item.classification.niche_label}</span>
                          )}
                          <span className="sub-row">
                            {featureLabel(item.classification.is_faceless_friendly, 'Faceless', 'Не faceless')}
                            {' · '}
                            {featureLabel(item.classification.is_ai_friendly, 'AI-friendly', 'Не AI')}
                          </span>
                        </>
                      ) : (
                        <span className="unclassified">Ещё не классифицирован</span>
                      )}
                    </td>
                    <td>
                      {item.channel_avg_views != null ? (
                        <div className="explain-block">
                          <div className="explain-line">Среднее канала: {formatCompact(item.channel_avg_views)}</div>
                          <div className="explain-line">Медиана канала: {formatCompact(item.channel_median_views)}</div>
                          <div className="explain-divider" />
                          {item.ratio_to_avg != null && (
                            <div className="explain-line explain-highlight">x{formatNumber(item.ratio_to_avg, 1)} к среднему</div>
                          )}
                          {item.ratio_to_median != null && (
                            <div className="explain-line explain-highlight">x{formatNumber(item.ratio_to_median, 1)} к медиане</div>
                          )}
                          <div className="explain-divider" />
                          <div className="explain-line explain-percentile">
                            {item.percentile_bucket === 'top_10_percent' ? 'Топ 10% канала' :
                             item.percentile_bucket === 'top_25_percent' ? 'Топ 25% канала' :
                             item.percentile_bucket === 'normal' ? 'Обычный диапазон' : ''}
                          </div>
                        </div>
                      ) : (
                        <span className="explain-missing">Недостаточно данных по каналу для расчета базовой статистики.</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : data && data.length === 0 ? (
          <div className="empty-state">
            <p className="title">Аномалий не найдено</p>
            <p>Попробуйте увеличить глубину синхронизации, добавить больше каналов или снизить минимальную аномальность. Прорывы малых каналов появляются только если видео сильно обгоняет размер канала.</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
