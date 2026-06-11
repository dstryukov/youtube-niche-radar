'use client';

import { useState, useCallback } from 'react';
import { getOutliers } from '../lib/api';
import type { Outlier, OutlierFilters } from '../lib/api';
import { formatNumber, formatViewsPerDay, formatSubscribers } from '../lib/format';

const DEFAULT_FILTERS: OutlierFilters = {
  limit: 25,
};

type SelectFilter = {
  faceless: '' | 'yes' | 'no';
  ai: '' | 'yes' | 'no';
};

export default function OutlierExplorer() {
  const [data, setData] = useState<Outlier[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [minScore, setMinScore] = useState('');
  const [smallBreakout, setSmallBreakout] = useState(false);
  const [formatLabel, setFormatLabel] = useState('');
  const [nicheLabel, setNicheLabel] = useState('');
  const [faceless, setFaceless] = useState<SelectFilter['faceless']>('');
  const [ai, setAi] = useState<SelectFilter['ai']>('');
  const [sort, setSort] = useState<OutlierFilters['sort']>('outlier_score');

  const fetchData = useCallback(async (filters: OutlierFilters) => {
    setLoading(true);
    setError(null);
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
    return f;
  }, [minScore, smallBreakout, formatLabel, nicheLabel, faceless, ai, sort]);

  const handleApply = () => {
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
    fetchData(DEFAULT_FILTERS);
  };

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

  return (
    <div className="outlier-explorer">
      <div className="filter-panel">
        <div className="filter-grid">
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
            </select>
          </div>
          <div className="filter-item filter-actions">
            <label className="filter-label">&nbsp;</label>
            <div className="filter-btn-row">
              <button className="btn btn-primary" onClick={handleApply}>Применить</button>
              <button className="btn btn-secondary" onClick={handleReset}>Сбросить</button>
            </div>
          </div>
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
          <table className="table">
            <thead>
              <tr>
                <th>Видео</th>
                <th>Канал</th>
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
                    {item.outlier_multiplier != null ? `x${formatNumber(item.outlier_multiplier, 1)}` : '—'}
                    <span className="sub-row">{formatViewsPerDay(item.views_per_day)}</span>
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
                  <td><span className="explanation">{item.explanation ?? '—'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : data && data.length === 0 ? (
          <div className="empty-state">
            <p className="title">Аномалий не найдено</p>
            <p>Попробуйте изменить фильтры</p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
