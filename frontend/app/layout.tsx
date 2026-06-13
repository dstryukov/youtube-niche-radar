import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = {
  title: 'MVP-радар — YouTube Niche Radar',
  description: 'Поиск YouTube-ниш, аномальных роликов, форматов и идей для адаптации'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <nav className="nav-bar">
          <a href="/" className="nav-logo">YouTube Niche Radar</a>
          <div className="nav-links">
            <a href="/" className="nav-link">Главная</a>
            <a href="/analytics/formats" className="nav-link">Форматы</a>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
