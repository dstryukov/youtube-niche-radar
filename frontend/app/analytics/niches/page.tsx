import { getNicheCoverage, getNicheStats } from '../../../lib/api';
import NicheDashboard from '../../../components/NicheDashboard';

export default async function NichesPage() {
  const [stats, coverage] = await Promise.all([
    getNicheStats().catch(() => null),
    getNicheCoverage().catch(() => null),
  ]);

  return (
    <main className="shell">
      <section className="header">
        <div>
          <p className="eyebrow">Аналитика</p>
          <h1>Ниши</h1>
          <p className="muted">Статистика по нишам видео: распределение, рост и лучшие аномалии</p>
        </div>
        <a href="/" className="btn btn-secondary btn-sm">← На главную</a>
      </section>

      <NicheDashboard />
    </main>
  );
}
