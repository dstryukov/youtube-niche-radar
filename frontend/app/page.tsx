import { getDashboardSummary } from '../lib/api';
import { formatNumber } from '../lib/format';
import ChannelManager from '../components/ChannelManager';
import FormatDashboard from '../components/FormatDashboard';
import TaskList from '../components/TaskList';
import OutlierExplorer from '../components/OutlierExplorer';

export default async function Page() {
  const summary = await getDashboardSummary().catch(() => null);

  return (
    <main className="shell">
      <section className="header">
        <div>
          <p className="eyebrow">MVP-радар</p>
          <h1>YouTube Niche Radar</h1>
          <p className="muted">Ниши, форматы, аномальные ролики и прорывы малых каналов</p>
        </div>
      </section>

      <section className="grid">
        {summary ? (
          <>
            <Card label="Каналы" metric={formatNumber(summary.channels_count, 0)} hint="Отслеживаемые каналы" />
            <Card label="Видео" metric={formatNumber(summary.videos_count, 0)} hint="Собранные ролики" />
            <Card label="Прорывы малых каналов" metric={formatNumber(summary.small_channel_breakouts_count, 0)} hint="Видео малых каналов, которые набрали непропорционально много просмотров." />
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
        <h2>Каталог форматов</h2>
        <FormatDashboard />
      </section>

      <section className="panel">
        <h2>Управление каналами</h2>
        <ChannelManager />
      </section>

      <section className="panel">
        <h2>Последние задачи</h2>
        <TaskList />
      </section>

      <section className="panel">
        <h2>Главные аномалии</h2>
        <OutlierExplorer />
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
