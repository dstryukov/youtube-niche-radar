import { getDashboardSummary, getOutliers } from '../lib/api';
import { formatNumber, formatViewsPerDay, formatSubscribers } from '../lib/format';

export default async function Page() {
  const [summary, outliers] = await Promise.all([
    getDashboardSummary().catch(() => null),
    getOutliers().catch(() => []),
  ]);

  return (
    <main className="shell">
      <section className="header">
        <div>
          <p className="eyebrow">MVP-радар</p>
          <h1>YouTube Niche Radar</h1>
          <p className="muted">Ниши, форматы, аномальные ролики и small channel breakouts</p>
        </div>
      </section>

      <section className="grid">
        {summary ? (
          <>
            <Card label="Каналы" metric={formatNumber(summary.channels_count, 0)} hint="Отслеживаемые каналы" />
            <Card label="Видео" metric={formatNumber(summary.videos_count, 0)} hint="Собранные ролики" />
            <Card label="Прорывы малых каналов" metric={formatNumber(summary.small_channel_breakouts_count, 0)} hint="Видео, резко обогнавшие размер канала" />
            <Card label="Средняя аномальность" metric={formatNumber(summary.avg_outlier_score)} hint="Средний outlier score по базе" />
          </>
        ) : (
          <>
            <ErrorCard label="Каналы" hint="Не удалось загрузить" />
            <ErrorCard label="Видео" hint="Не удалось загрузить" />
            <ErrorCard label="Прорывы малых каналов" hint="Не удалось загрузить" />
            <ErrorCard label="Средняя аномальность" hint="Не удалось загрузить" />
          </>
        )}
      </section>

      <section className="panel">
        <h2>Главные аномалии</h2>
        {outliers.length > 0 ? (
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
              {outliers.map((item) => (
                <tr key={item.video_id}>
                  <td>
                    <a className="video-title" href={item.url} target="_blank" rel="noopener noreferrer">{item.title}</a>
                    <span className="sub-row">{item.channel_title ?? '—'}</span>
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
        ) : (
          <div className="empty-state">
            <p className="title">Аномалий пока нет</p>
            <p>Добавьте каналы и запустите синхронизацию,<br />чтобы увидеть прорывные ролики</p>
          </div>
        )}
      </section>
    </main>
  );
}

function Card({ label, metric, hint }: { label: string; metric: string; hint: string }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className="metric">{metric}</div>
      <div className="hint">{hint}</div>
    </div>
  );
}

function ErrorCard({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="error-card">
      <div className="label">{label}</div>
      <div className="metric">—</div>
      <div className="hint">{hint}</div>
    </div>
  );
}

function featureLabel(value: boolean | null, ifTrue: string, ifFalse: string): string {
  if (value === true) return ifTrue;
  if (value === false) return ifFalse;
  return 'Неизвестно';
}
