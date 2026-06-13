import { getFormatStats } from '../../../lib/api';
import { formatCompact, formatNumber } from '../../../lib/format';

export default async function FormatsPage() {
  const stats = await getFormatStats().catch(() => null);

  return (
    <main className="shell">
      <section className="header">
        <div>
          <p className="eyebrow">Аналитика</p>
          <h1>Форматы</h1>
          <p className="muted">Статистика по форматам видео: распределение, аномальность и средние просмотры</p>
        </div>
        <a href="/" className="btn btn-secondary btn-sm">← На главную</a>
      </section>

      <section className="panel">
        <h2>Статистика форматов</h2>
        {stats && stats.length > 0 ? (
          <div className="analytics-table-wrap">
            <table className="table analytics-table">
              <thead>
                <tr>
                  <th>Формат</th>
                  <th>Количество видео</th>
                  <th>Средний Outlier Score</th>
                  <th>Средние просмотры</th>
                </tr>
              </thead>
              <tbody>
                {stats.map((row) => (
                  <tr key={row.format_label}>
                    <td>
                      <span className="badge badge-format">{row.format_label}</span>
                    </td>
                    <td className="num-cell">{formatNumber(row.videos, 0)}</td>
                    <td className="num-cell">{row.avg_outlier_score != null ? formatNumber(row.avg_outlier_score, 2) : '—'}</td>
                    <td className="num-cell">{row.avg_views != null ? formatCompact(row.avg_views) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p className="title">Нет данных по форматам</p>
            <p>Добавьте каналы и выполните синхронизацию, чтобы увидеть статистику форматов.</p>
          </div>
        )}
      </section>
    </main>
  );
}
