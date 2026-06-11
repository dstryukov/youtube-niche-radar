import { getDashboardSummary, getOutliers } from '../lib/api';

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en', { maximumFractionDigits: 1 }).format(value);
}

export default async function Page() {
  const [summary, outliers] = await Promise.all([
    getDashboardSummary().catch(() => null),
    getOutliers().catch(() => [])
  ]);

  return (
    <main className="shell">
      <section className="header">
        <div>
          <p className="eyebrow">MVP dashboard</p>
          <h1>YouTube Niche Radar</h1>
          <p className="muted">Ниши, форматы, аномальные ролики и small channel breakouts.</p>
        </div>
        <div className="card">
          <div className="label">API</div>
          <div className="metric">localhost:8000</div>
        </div>
      </section>

      <section className="grid">
        <div className="card"><div className="label">Channels</div><div className="metric">{summary?.channels_count ?? '—'}</div></div>
        <div className="card"><div className="label">Videos</div><div className="metric">{summary?.videos_count ?? '—'}</div></div>
        <div className="card"><div className="label">Breakouts</div><div className="metric">{summary?.small_channel_breakouts_count ?? '—'}</div></div>
        <div className="card"><div className="label">Avg outlier score</div><div className="metric">{formatNumber(summary?.avg_outlier_score)}</div></div>
      </section>

      <section className="panel">
        <h2>Top outliers</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Video</th>
              <th>Channel</th>
              <th>Score</th>
              <th>Format</th>
              <th>Why anomaly</th>
            </tr>
          </thead>
          <tbody>
            {outliers.map((item) => (
              <tr key={item.video_id}>
                <td><a href={item.url} target="_blank">{item.title}</a></td>
                <td>{item.channel_title ?? '—'}<br /><span className="muted">{formatNumber(item.channel_subscribers)} subs</span></td>
                <td>x{formatNumber(item.outlier_multiplier)}<br /><span className="muted">{formatNumber(item.views_per_day)} views/day</span></td>
                <td><span className="badge">{item.classification?.format_label ?? 'unclassified'}</span></td>
                <td>{item.explanation ?? '—'}</td>
              </tr>
            ))}
            {outliers.length === 0 && (
              <tr><td colSpan={5} className="muted">No outliers yet. Add channels and run sync.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
