'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { getChannels, createChannel, importChannelsCsv, syncChannel, syncAllChannels } from '../lib/api';
import type { Channel, ScanOptions } from '../lib/api';
import { formatCompact } from '../lib/format';

function parseChannelInput(input: string): { channel_id?: string; handle?: string } | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  if (/^UC[\w-]{22,}$/.test(trimmed)) {
    return { channel_id: trimmed };
  }

  if (trimmed.startsWith('@')) {
    return { handle: trimmed };
  }

  let urlStr = trimmed;
  if (!/^https?:\/\//i.test(urlStr)) {
    urlStr = 'https://' + urlStr;
  }

  try {
    const url = new URL(urlStr);
    if (url.hostname.includes('youtube.com') || url.hostname.includes('youtu.be')) {
      const path = url.pathname;

      const channelMatch = path.match(/\/channel\/(UC[\w-]+)/);
      if (channelMatch) return { channel_id: channelMatch[1] };

      const handleMatch = path.match(/\/@([\w.-]+)/);
      if (handleMatch) return { handle: '@' + handleMatch[1] };

      const segments = path.split('/').filter(Boolean);
      if (segments.length > 0) {
        const last = segments[segments.length - 1];
        if (last.startsWith('@')) return { handle: last };
        if (/^UC[\w-]+$/.test(last)) return { channel_id: last };
      }
    }
  } catch {
  }

  if (/^UC[\w-]+$/.test(trimmed)) {
    return { channel_id: trimmed };
  }

  return null;
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

type ScanPreset = {
  label: string;
  hint: string;
  opts: ScanOptions;
};

const SCAN_PRESETS: ScanPreset[] = [
  {
    label: 'Ранние сигналы',
    hint: 'Небольшие видео, которые быстро набирают просмотры. глубина 150, просмотры 1 000–10 000.',
    opts: { limit: 150, minViews: 1000, maxViews: 10000, stopAfterMatches: 20, saveSkipped: true },
  },
  {
    label: 'Проверенные форматы',
    hint: 'Форматы, уже доказавшие спрос. глубина 300, просмотры 10 000–100 000.',
    opts: { limit: 300, minViews: 10000, maxViews: 100000, stopAfterMatches: 30, saveSkipped: true },
  },
  {
    label: 'Свежие видео',
    hint: 'Свежие ролики с быстрым набором просмотров. глубина 150, от 500 просмотров/день.',
    opts: { limit: 150, minViewsPerDay: 500, publishedAfter: daysAgo(30), stopAfterMatches: 20, saveSkipped: true },
  },
  {
    label: 'Крупные хиты',
    hint: 'Крупные успешные форматы. глубина 300, от 100 000 просмотров.',
    opts: { limit: 300, minViews: 100000, stopAfterMatches: 20, saveSkipped: true },
  },
];

export default function ChannelManager() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [input, setInput] = useState('');
  const [adding, setAdding] = useState(false);
  const [syncAllLoading, setSyncAllLoading] = useState(false);
  const [syncingIds, setSyncingIds] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const [scanLimit, setScanLimit] = useState(150);
  const [scanMinViews, setScanMinViews] = useState('');
  const [scanMaxViews, setScanMaxViews] = useState('');
  const [scanMinVpd, setScanMinVpd] = useState('');
  const [scanMaxVpd, setScanMaxVpd] = useState('');
  const [scanPublishedAfter, setScanPublishedAfter] = useState('');
  const [scanPublishedBefore, setScanPublishedBefore] = useState('');
  const [scanStopAfter, setScanStopAfter] = useState('');
  const [scanSaveSkipped, setScanSaveSkipped] = useState(true);

  const loadChannels = useCallback(async () => {
    try {
      const data = await getChannels();
      setChannels(data);
    } catch {
      showError('Не удалось загрузить список каналов');
    }
  }, []);

  useEffect(() => { loadChannels(); }, [loadChannels]);

  const showError = (msg: string) => { setError(msg); setSuccess(null); };
  const showSuccess = (msg: string) => { setSuccess(msg); setError(null); };

  const getScanOptions = useCallback((): ScanOptions => {
    const opts: ScanOptions = { limit: scanLimit, saveSkipped: scanSaveSkipped };
    if (scanMinViews) {
      const n = parseInt(scanMinViews, 10);
      if (!isNaN(n)) opts.minViews = n;
    }
    if (scanMaxViews) {
      const n = parseInt(scanMaxViews, 10);
      if (!isNaN(n)) opts.maxViews = n;
    }
    if (scanMinVpd) {
      const n = parseFloat(scanMinVpd);
      if (!isNaN(n)) opts.minViewsPerDay = n;
    }
    if (scanMaxVpd) {
      const n = parseFloat(scanMaxVpd);
      if (!isNaN(n)) opts.maxViewsPerDay = n;
    }
    if (scanPublishedAfter) opts.publishedAfter = scanPublishedAfter + 'T00:00:00';
    if (scanPublishedBefore) opts.publishedBefore = scanPublishedBefore + 'T23:59:59';
    if (scanStopAfter) {
      const n = parseInt(scanStopAfter, 10);
      if (!isNaN(n)) opts.stopAfterMatches = n;
    }
    return opts;
  }, [scanLimit, scanMinViews, scanMaxViews, scanMinVpd, scanMaxVpd, scanPublishedAfter, scanPublishedBefore, scanStopAfter, scanSaveSkipped]);

  const applyPreset = (preset: ScanPreset) => {
    setScanLimit(preset.opts.limit ?? 150);
    setScanMinViews(preset.opts.minViews != null ? String(preset.opts.minViews) : '');
    setScanMaxViews(preset.opts.maxViews != null ? String(preset.opts.maxViews) : '');
    setScanMinVpd(preset.opts.minViewsPerDay != null ? String(preset.opts.minViewsPerDay) : '');
    setScanMaxVpd(preset.opts.maxViewsPerDay != null ? String(preset.opts.maxViewsPerDay) : '');
    setScanPublishedAfter(preset.opts.publishedAfter ? preset.opts.publishedAfter.split('T')[0] : '');
    setScanPublishedBefore(preset.opts.publishedBefore ? preset.opts.publishedBefore.split('T')[0] : '');
    setScanStopAfter(preset.opts.stopAfterMatches != null ? String(preset.opts.stopAfterMatches) : '');
    setScanSaveSkipped(preset.opts.saveSkipped ?? true);
  };

  const handleSync = async (channelId: number) => {
    showSuccess('');
    setSyncingIds(prev => new Set(prev).add(channelId));
    try {
      const opts = getScanOptions();
      const result = await syncChannel(channelId, opts);
      const parts = [`Сканирование запущено: до ${result.requested_limit ?? scanLimit} видео`];
      if (opts.minViews != null || opts.maxViews != null) {
        parts.push(`фильтр просмотров ${opts.minViews ?? 0}–${opts.maxViews ?? '∞'}`);
      }
      showSuccess(parts.join(', '));
      setTimeout(loadChannels, 3000);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось запустить синхронизацию');
    } finally {
      setSyncingIds(prev => {
        const next = new Set(prev);
        next.delete(channelId);
        return next;
      });
    }
  };

  const handleSyncAll = async () => {
    showSuccess('');
    setSyncAllLoading(true);
    try {
      const opts = getScanOptions();
      await syncAllChannels(opts);
      const parts = [`Сканирование всех каналов запущено: до ${scanLimit} видео`];
      if (opts.minViews != null || opts.maxViews != null) {
        parts.push(`фильтр просмотров ${opts.minViews ?? 0}–${opts.maxViews ?? '∞'}`);
      }
      showSuccess(parts.join(', '));
      setTimeout(loadChannels, 3000);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось запустить синхронизацию всех каналов');
    } finally {
      setSyncAllLoading(false);
    }
  };

  const handleAddChannel = async () => {
    const parsed = parseChannelInput(input);
    if (!parsed) { showError('Не удалось распознать канал. Укажите Channel ID (UC...), @handle или ссылку.'); return; }
    setAdding(true);
    showSuccess('');
    try {
      await createChannel(parsed);
      setInput('');
      showSuccess('Канал добавлен');
      setTimeout(loadChannels, 2000);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось добавить канал');
    } finally {
      setAdding(false);
    }
  };

  const handleImportCsv = async () => {
    if (!csvFile) return;
    setImporting(true);
    showSuccess('');
    try {
      await importChannelsCsv(csvFile);
      setCsvFile(null);
      if (fileRef.current) fileRef.current.value = '';
      showSuccess('CSV импортирован');
      setTimeout(loadChannels, 2000);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось импортировать CSV');
    } finally {
      setImporting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleAddChannel();
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="channel-manager">
      <div className="channel-controls">
        <div className="form-row">
          <input
            className="input"
            type="text"
            placeholder="Channel ID (UC...), @handle или ссылка на YouTube"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={adding}
          />
          <button className="btn btn-primary" onClick={handleAddChannel} disabled={adding || !input.trim()}>
            {adding ? 'Добавление…' : 'Добавить канал'}
          </button>
        </div>

        <div className="form-row form-row-actions">
          <div className="file-wrapper">
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={e => setCsvFile(e.target.files?.[0] ?? null)}
              className="file-input"
              id="csv-upload"
            />
            <label htmlFor="csv-upload" className="file-label">
              {csvFile ? csvFile.name : 'Выберите CSV-файл'}
            </label>
          </div>
          <button className="btn btn-secondary" onClick={handleImportCsv} disabled={!csvFile || importing}>
            {importing ? 'Импорт…' : 'Импортировать CSV'}
          </button>
        </div>
      </div>

      <div className="sync-settings">
        <h3 className="sync-settings-title">Настройки сканирования</h3>
        <div className="sync-settings-grid">
          <div className="sync-field">
            <label className="sync-field-label">Глубина</label>
            <select className="select" value={scanLimit} onChange={e => setScanLimit(Number(e.target.value))}>
              <option value={50}>50 видео</option>
              <option value={100}>100 видео</option>
              <option value={150}>150 видео</option>
              <option value={300}>300 видео</option>
              <option value={500}>500 видео</option>
            </select>
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Просмотры от</label>
            <input className="input" type="number" min="0" placeholder="0" value={scanMinViews} onChange={e => setScanMinViews(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Просмотры до</label>
            <input className="input" type="number" min="0" placeholder="∞" value={scanMaxViews} onChange={e => setScanMaxViews(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Просмотров/день от</label>
            <input className="input" type="number" min="0" step="0.1" placeholder="0" value={scanMinVpd} onChange={e => setScanMinVpd(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Просмотров/день до</label>
            <input className="input" type="number" min="0" step="0.1" placeholder="∞" value={scanMaxVpd} onChange={e => setScanMaxVpd(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Опубликовано после</label>
            <input className="input" type="date" value={scanPublishedAfter} onChange={e => setScanPublishedAfter(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Опубликовано до</label>
            <input className="input" type="date" value={scanPublishedBefore} onChange={e => setScanPublishedBefore(e.target.value)} />
          </div>
          <div className="sync-field">
            <label className="sync-field-label">Остановиться после N подходящих</label>
            <input className="input" type="number" min="1" placeholder="оставить пустым" value={scanStopAfter} onChange={e => setScanStopAfter(e.target.value)} />
          </div>
          <div className="sync-field sync-field-check">
            <label className="checkbox-label">
              <input type="checkbox" checked={scanSaveSkipped} onChange={e => setScanSaveSkipped(e.target.checked)} />
              Сохранять неподходящие видео для baseline
            </label>
          </div>
          <div className="sync-field sync-field-actions">
            <button className="btn btn-accent" onClick={handleSyncAll} disabled={syncAllLoading || channels.length === 0}>
              {syncAllLoading ? 'Сканирование…' : 'Синхронизировать все'}
            </button>
          </div>
        </div>
        <p className="sync-settings-hint">Глубина сканирования экономит YouTube API quota сильнее всего. Фильтры по просмотрам применяются после получения статистики и помогают остановить сканирование раньше, если найдено достаточно подходящих видео.</p>
      </div>

      <div className="scan-presets">
        <h4 className="scan-presets-title">Рекомендации</h4>
        <div className="preset-buttons">
          {SCAN_PRESETS.map(p => (
            <button key={p.label} className="btn btn-sm btn-outline preset-btn" onClick={() => applyPreset(p)} title={p.hint}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="message message-error">{error}</div>}
      {success && <div className="message message-success">{success}</div>}

      <div className="channel-table-wrap">
        <table className="table channel-table">
          <thead>
            <tr>
              <th>Канал</th>
              <th>Handle</th>
              <th>Подписчики</th>
              <th>Видео</th>
              <th>Последняя синх.</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {channels.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-cell">Каналов пока нет. Добавьте первый канал выше.</td>
              </tr>
            ) : (
              channels.map(ch => (
                <tr key={ch.id}>
                  <td><span className="channel-title">{ch.title ?? ch.youtube_channel_id}</span></td>
                  <td><span className="channel-handle">{ch.handle ?? '—'}</span></td>
                  <td>{ch.subscriber_count != null ? formatCompact(ch.subscriber_count) : '—'}</td>
                  <td>{ch.video_count != null ? String(ch.video_count) : '—'}</td>
                  <td><span className="last-sync">{formatDate(ch.last_synced_at)}</span></td>
                  <td>
                    <button
                      className="btn btn-sm btn-outline"
                      onClick={() => handleSync(ch.id)}
                      disabled={syncingIds.has(ch.id)}
                    >
                      {syncingIds.has(ch.id) ? '…' : 'Синхронизировать'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
