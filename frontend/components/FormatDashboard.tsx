'use client';

import { useState, useEffect, useCallback } from 'react';
import { getFormats, getTrendingFormats, getFormatDetail } from '../lib/api';
import type { FormatSummary, FormatDetail, TrendingFormat } from '../lib/api';
import { formatNumber, formatCompact } from '../lib/format';

type Period = 7 | 30 | 90;

export default function FormatDashboard() {
  const [period, setPeriod] = useState<Period>(30);
  const [formats, setFormats] = useState<FormatSummary[] | null>(null);
  const [trending, setTrending] = useState<TrendingFormat[] | null>(null);
  const [detail, setDetail] = useState<FormatDetail | null>(null);
  const [detailLabel, setDetailLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: Period) => {
    setLoading(true);
    setError(null);
    try {
      const [f, t] = await Promise.all([getFormats(), getTrendingFormats(p)]);
      setFormats(f);
      setTrending(t);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить данные по форматам');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(period); }, [period, load]);

  const openDetail = async (label: string) => {
    setDetailLabel(label);
    setDetail(null);
    try {
      const d = await getFormatDetail(label, period);
      setDetail(d);
    } catch {
      setDetail(null);
    }
  };

  const closeDetail = () => {
    setDetail(null);
    setDetailLabel(null);
  };

  const percent = (count: number, total: number) => {
    if (total === 0) return '—';
    return (count / total * 100).toFixed(0) + '%';
  };

  if (loading) {
    return (
      <div className="format-loading">
        <div className="spinner" />
        <span>Загрузка форматов…</span>
      </div>
    );
  }

  if (error) {
    return <div className="message message-error">{error}</div>;
  }

  return (
    <div className="format-dashboard">
      <div className="period-tabs">
        {[7, 30, 90].map(p => (
          <button
            key={p}
            className={`btn btn-sm ${period === p ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setPeriod(p as Period)}
          >
            {p} дней
          </button>
        ))}
      </div>

      {trending && trending.length > 0 && (
        <div className="trending-section">
          <h3 className="section-title">В тренде</h3>
          <div className="trending-grid">
            {trending.map(t => (
              <button
                key={t.format_label}
                className="trending-card"
                onClick={() => openDetail(t.format_label)}
              >
                <div className="trending-label">{t.format_label}</div>
                <div className="trending-stats">
                  <span className="trending-count">{t.video_count} видео</span>
                  <span className={`trending-growth ${t.growth_rate > 0 ? 'trending-up' : 'trending-down'}`}>
                    {t.growth_rate > 0 ? '+' : ''}{t.growth_rate}%
                  </span>
                </div>
                {t.avg_views != null && (
                  <div className="trending-views">{formatCompact(t.avg_views)} просмотров</div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {formats && formats.length > 0 && (
        <div className="formats-table-section">
          <h3 className="section-title">Топ форматов</h3>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Формат</th>
                  <th>Видео</th>
                  <th>Средние просмотры</th>
                  <th>Avg outlier</th>
                  <th>Faceless</th>
                  <th>AI-friendly</th>
                </tr>
              </thead>
              <tbody>
                {formats.map(f => (
                  <tr key={f.format_label} className="clickable-row" onClick={() => openDetail(f.format_label)}>
                    <td><span className="format-label">{f.format_label}</span></td>
                    <td>{formatNumber(f.videos, 0)}</td>
                    <td>{f.avg_views != null ? formatCompact(f.avg_views) : '—'}</td>
                    <td>{f.avg_outlier_score != null ? formatNumber(f.avg_outlier_score, 2) : '—'}</td>
                    <td>{percent(f.faceless_count, f.videos)}</td>
                    <td>{percent(f.ai_friendly_count, f.videos)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && formats && formats.length === 0 && (
        <div className="empty-state">
          <p className="title">Классифицированных видео пока нет</p>
          <p>Форматы появятся после классификации видео через кнопку "Классифицировать" в разделе аномалий.</p>
        </div>
      )}

      {detail && (
        <div className="modal-overlay" onClick={closeDetail}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{detail.format_label}</h3>
              <button className="btn btn-sm btn-secondary" onClick={closeDetail}>Закрыть</button>
            </div>
            <div className="modal-body">
              {detail.description && <p className="format-description">{detail.description}</p>}
              {detail.classifier_version && (
                <span className="badge badge-sm badge-gray" style={{ marginBottom: '12px' }}>{detail.classifier_version}</span>
              )}

              <div className="detail-grid">
                <div className="detail-card">
                  <div className="detail-metric">{formatNumber(detail.videos_count, 0)}</div>
                  <div className="detail-label">Видео</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.avg_views != null ? formatCompact(detail.avg_views) : '—'}</div>
                  <div className="detail-label">Средние просмотры</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.median_views != null ? formatCompact(detail.median_views) : '—'}</div>
                  <div className="detail-label">Медиана просмотров</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.max_views != null ? formatCompact(detail.max_views) : '—'}</div>
                  <div className="detail-label">Макс просмотры</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.avg_outlier_score != null ? formatNumber(detail.avg_outlier_score, 2) : '—'}</div>
                  <div className="detail-label">Avg outlier score</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.avg_repeatability != null ? formatNumber(detail.avg_repeatability, 2) : '—'}</div>
                  <div className="detail-label">Avg повторяемость</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.is_faceless_friendly ? 'Да' : detail.is_faceless_friendly === false ? 'Нет' : '—'}</div>
                  <div className="detail-label">Faceless</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.is_ai_friendly ? 'Да' : detail.is_ai_friendly === false ? 'Нет' : '—'}</div>
                  <div className="detail-label">AI-friendly</div>
                </div>
                <div className="detail-card">
                  <div className="detail-metric">{detail.repeatability_prior != null ? formatNumber(detail.repeatability_prior, 2) : '—'}</div>
                  <div className="detail-label">Repeatability prior</div>
                </div>
                <div className="detail-card detail-card-wide">
                  <div className="detail-metric">{detail.trend != null ? (detail.trend > 0 ? '+' : '') + detail.trend + '%' : '—'}</div>
                  <div className="detail-label">Тренд за период</div>
                </div>
              </div>

              {detail.top_channels && detail.top_channels.length > 0 && (
                <div className="top-channels-section">
                  <h4>Топ каналов по формату</h4>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Канал</th>
                        <th>Видео</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.top_channels.map(ch => (
                        <tr key={ch.channel_title}>
                          <td>{ch.channel_title}</td>
                          <td>{formatNumber(ch.videos_count, 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
