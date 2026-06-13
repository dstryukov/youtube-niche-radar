'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getNicheStats, getTrendingNiches, getNicheCoverage, getNicheOutliers, reclassifyNiches, NICHE_OPTIONS } from '../lib/api';
import type { NicheStats, TrendingNiche, NicheCoverage, Outlier } from '../lib/api';
import { formatNumber, formatCompact } from '../lib/format';

export default function NicheDashboard() {
  const [stats, setStats] = useState<NicheStats[] | null>(null);
  const [trending, setTrending] = useState<TrendingNiche[] | null>(null);
  const [coverage, setCoverage] = useState<NicheCoverage | null>(null);
  const [outliers, setOutliers] = useState<Outlier[] | null>(null);
  const [outlierNiche, setOutlierNiche] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reclassifying, setReclassifying] = useState(false);
  const [reclassifyMsg, setReclassifyMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, t, c] = await Promise.all([
        getNicheStats().catch(() => null),
        getTrendingNiches().catch(() => null),
        getNicheCoverage().catch(() => null),
      ]);
      setStats(s);
      setTrending(t);
      setCoverage(c);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить данные ниш');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openOutliers = async (niche: string) => {
    setOutlierNiche(niche);
    setOutliers(null);
    try {
      const data = await getNicheOutliers(niche);
      setOutliers(data);
    } catch {
      setOutliers([]);
    }
  };

  const closeOutliers = () => {
    setOutliers(null);
    setOutlierNiche(null);
  };

  const handleReclassify = async () => {
    setReclassifying(true);
    setReclassifyMsg(null);
    try {
      const result = await reclassifyNiches();
      setReclassifyMsg(`Обработано: ${result.videos_processed}, обновлено: ${result.updated}, ошибок: ${result.failed}`);
      load();
    } catch (e) {
      setReclassifyMsg(e instanceof Error ? e.message : 'Ошибка переклассификации');
    } finally {
      setReclassifying(false);
    }
  };

  const growthColor = (rate: number): string => {
    if (rate > 50) return 'badge-green';
    if (rate >= 20) return 'badge-yellow';
    return 'badge-gray';
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  const formatViews = (views: number | null | undefined): string => {
    if (views == null) return '—';
    if (views >= 1_000_000) return (views / 1_000_000).toFixed(1).replace('.', ',') + ' млн просмотров';
    if (views >= 1_000) return (views / 1_000).toFixed(1).replace('.', ',') + ' тыс. просмотров';
    return String(views) + ' просмотров';
  };

  if (loading) {
    return (
      <div className="outlier-loading">
        <div className="spinner" />
        <span>Загрузка ниш…</span>
      </div>
    );
  }

  if (error) {
    return <div className="message message-error">{error}</div>;
  }

  return (
    <>
      {coverage && (
        <section className="panel">
          <div className="coverage-card">
            <h2>Покрытие классификации</h2>
            <div className="coverage-metric">{coverage.coverage_percent}%</div>
            <div className="coverage-detail">{formatNumber(coverage.classified, 0)} / {formatNumber(coverage.videos_total, 0)} видео</div>
            {coverage.other > 0 && (
              <div className="coverage-detail" style={{ color: '#98a2b3', fontSize: '12px', marginTop: '2px' }}>
                {formatNumber(coverage.other, 0)} в категории &laquo;Другое&raquo;
              </div>
            )}
          </div>
        </section>
      )}

      {trending && trending.length > 0 && (
        <section className="panel">
          <h2>Растущие ниши</h2>
          <div className="trending-grid" style={{ padding: '16px 20px' }}>
            {trending.slice(0, 6).map(t => (
              <div
                key={t.niche}
                className="trending-card"
                onClick={() => openOutliers(t.niche)}
                style={{ cursor: 'pointer' }}
              >
                <div className="trending-label">{t.niche}</div>
                <div className="trending-stats">
                  <span className={`trending-growth ${t.growth_rate > 0 ? 'trending-up' : 'trending-down'}`}>
                    {t.growth_rate > 0 ? '+' : ''}{t.growth_rate}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 20px', borderBottom: '1px solid #eaecf0' }}>
          <h2 style={{ margin: 0, padding: 0, borderBottom: 'none' }}>Статистика ниш</h2>
          <button className="btn btn-sm btn-accent" onClick={handleReclassify} disabled={reclassifying}>
            {reclassifying ? '…' : 'Переклассифицировать'}
          </button>
        </div>
        {reclassifyMsg && (
          <div className="message message-success" style={{ margin: '12px 20px' }}>{reclassifyMsg}</div>
        )}
        {stats && stats.length > 0 ? (
          <div className="analytics-table-wrap">
            <table className="table analytics-table">
              <thead>
                <tr>
                  <th>Ниша</th>
                  <th>Каналов</th>
                  <th>Видео</th>
                  <th>Аномалий</th>
                  <th>Средний Outlier</th>
                  <th>Средние просмотры</th>
                  <th>Рост</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((row) => (
                  <tr key={row.niche} className="clickable-row" onClick={() => openOutliers(row.niche)}>
                    <td>
                      <span className="badge badge-format">{row.niche}</span>
                    </td>
                    <td className="num-cell">{formatNumber(row.channels, 0)}</td>
                    <td className="num-cell">{formatNumber(row.videos, 0)}</td>
                    <td className="num-cell">{formatNumber(row.outliers, 0)}</td>
                    <td className="num-cell">{formatNumber(row.avg_outlier_score, 2)}</td>
                    <td className="num-cell">{formatCompact(row.avg_views)}</td>
                    <td className="num-cell">
                      <span className={`badge ${growthColor(row.growth_rate)}`}>
                        {row.growth_rate > 0 ? '+' : ''}{row.growth_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p className="title">Нет данных по нишам</p>
            <p>Добавьте каналы и выполните синхронизацию, чтобы увидеть статистику ниш.</p>
          </div>
        )}
      </section>

      {outlierNiche && (
        <div className="modal-overlay" onClick={closeOutliers}>
          <div className="modal-content modal-content-wide" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Лучшие аномалии: {outlierNiche}</h3>
              <button className="btn btn-sm btn-secondary" onClick={closeOutliers}>Закрыть</button>
            </div>
            <div className="modal-body">
              {outliers && outliers.length > 0 ? (
                <div className="outlier-table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Видео</th>
                        <th>Канал</th>
                        <th>Просмотры</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {outliers.map((item) => (
                        <tr key={item.video_id}>
                          <td>
                            <a className="video-title" href={item.url} target="_blank" rel="noopener noreferrer">{item.title}</a>
                            <span className="sub-row">{item.channel_title ?? '—'} · {formatDate(item.published_at)}</span>
                          </td>
                          <td>
                            <span className="channel-name">
                              {item.channel_subscribers != null
                                ? formatCompact(item.channel_subscribers) + ' подписчиков'
                                : '—'}
                            </span>
                            {item.is_small_channel_breakout && (
                              <span className="sub-row"><span className="badge badge-green">Малый канал</span></span>
                            )}
                          </td>
                          <td>
                            <span className="views-count">{formatViews(item.latest_views)}</span>
                          </td>
                          <td>
                            <span className="sub-row">Score: <strong>{item.outlier_score != null ? formatNumber(item.outlier_score, 2) : '—'}</strong></span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : outliers && outliers.length === 0 ? (
                <div className="empty-state">
                  <p className="title">Аномалий не найдено</p>
                  <p>В этой нише пока нет аномалий.</p>
                </div>
              ) : (
                <div className="outlier-loading">
                  <div className="spinner" />
                  <span>Загрузка аномалий…</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
