import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = {
  title: 'MVP-радар — YouTube Niche Radar',
  description: 'Поиск YouTube-ниш, аномальных роликов, форматов и идей для адаптации'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
