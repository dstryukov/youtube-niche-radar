import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = {
  title: 'YouTube Niche Radar',
  description: 'Dashboard for YouTube niches, outliers, formats, and breakouts'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
