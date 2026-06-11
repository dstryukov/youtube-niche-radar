'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { getChannels, createChannel, importChannelsCsv, syncChannel, syncAllChannels } from '../lib/api';
import type { Channel } from '../lib/api';
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
  const [syncLimit, setSyncLimit] = useState(150);
  const fileRef = useRef<HTMLInputElement>(null);

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

  const handleAddChannel = async () => {
    showSuccess('');
    const parsed = parseChannelInput(input);
    if (!parsed) {
      showError('Не удалось распознать канал. Введите channel_id (UC...), @handle или ссылку на YouTube.');
      return;
    }
    setAdding(true);
    try {
      const channel = await createChannel(parsed);
      setChannels(prev => [channel, ...prev]);
      setInput('');
      showSuccess(`Канал "${channel.title ?? channel.handle ?? channel.youtube_channel_id}" добавлен`);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось добавить канал');
    } finally {
      setAdding(false);
    }
  };

  const handleImportCsv = async () => {
    if (!csvFile) {
      showError('Выберите CSV-файл');
      return;
    }
    showSuccess('');
    setImporting(true);
    try {
      const result = await importChannelsCsv(csvFile);
      setChannels(prev => {
        const seen = new Set(prev.map(c => c.id));
        const newOnes = result.channels.filter(c => !seen.has(c.id));
        return [...newOnes, ...prev];
      });
      const parts = [`Импортировано: ${result.imported}`, `пропущено: ${result.skipped}`];
      if (result.errors.length > 0) parts.push(`ошибок: ${result.errors.length}`);
      showSuccess(parts.join(', '));
      setCsvFile(null);
      if (fileRef.current) fileRef.current.value = '';
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось импортировать CSV');
    } finally {
      setImporting(false);
    }
  };

  const handleSync = async (channelId: number) => {
    showSuccess('');
    setSyncingIds(prev => new Set(prev).add(channelId));
    try {
      const result = await syncChannel(channelId, syncLimit);
      showSuccess(`Синхронизация запущена: до ${result.requested_limit ?? syncLimit} последних видео.`);
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
      const result = await syncAllChannels(syncLimit);
      showSuccess(`Синхронизация всех каналов запущена: до ${syncLimit} видео на канал.`);
      setTimeout(loadChannels, 3000);
    } catch (e) {
      showError(e instanceof Error ? e.message : 'Не удалось запустить синхронизацию всех каналов');
    } finally {
      setSyncAllLoading(false);
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
        <h3 className="sync-settings-title">Настройки синхронизации</h3>
        <div className="sync-settings-body">
          <div className="sync-settings-field">
            <label className="sync-settings-label">Сколько последних видео сканировать</label>
            <div className="sync-settings-row">
              <select
                className="select sync-settings-select"
                value={syncLimit}
                onChange={e => setSyncLimit(Number(e.target.value))}
              >
                <option value={50}>50 видео</option>
                <option value={100}>100 видео</option>
                <option value={150}>150 видео</option>
                <option value={300}>300 видео</option>
                <option value={500}>500 видео</option>
              </select>
              <button className="btn btn-accent" onClick={handleSyncAll} disabled={syncAllLoading || channels.length === 0}>
                {syncAllLoading ? 'Синхронизация…' : 'Синхронизировать все'}
              </button>
            </div>
          </div>
          <p className="sync-settings-hint">Чем больше глубина, тем точнее поиск аномалий, но тем выше расход YouTube API quota.</p>
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
