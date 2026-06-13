'use client';

import { useState, useEffect, useCallback } from 'react';
import { getTasks } from '../lib/api';
import type { TaskRun } from '../lib/api';

const STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает',
  running: 'Выполняется',
  success: 'Успешно',
  failed: 'Ошибка',
  queued: 'В очереди',
};

const STATUS_CLASS: Record<string, string> = {
  pending: 'badge badge-gray',
  running: 'badge badge-yellow',
  success: 'badge badge-green',
  failed: 'badge badge-red',
  queued: 'badge badge-gray',
};

const TASK_TYPE_LABELS: Record<string, string> = {
  sync_channel: 'Синхронизация канала',
  classify_outliers: 'Классификация',
  classify_channel: 'Классификация канала',
};

const STOPPED_REASON_LABELS: Record<string, string> = {
  limit_reached: 'достигнут лимит',
  no_more_videos: 'видео закончились',
  stop_after_matches_reached: 'найдено достаточно видео',
};

function formatTaskType(type: string): string {
  return TASK_TYPE_LABELS[type] ?? type;
}

export default function TaskList() {
  const [tasks, setTasks] = useState<TaskRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTasks(10);
      setTasks(data);
    } catch {
      setError('Не удалось загрузить список задач');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString('ru-RU');
    } catch {
      return dateStr;
    }
  };

  const stoppedReasonLabel = (reason: string | null | undefined): string => {
    if (!reason) return '';
    return STOPPED_REASON_LABELS[reason] ?? reason;
  };

  return (
    <div className="task-list-section">
      <div className="task-list-header">
        <button className="btn btn-sm btn-secondary" onClick={loadTasks} disabled={loading}>
          {loading ? '…' : 'Обновить'}
        </button>
      </div>
      {error ? (
        <div className="message message-error" style={{ margin: '16px' }}>{error}</div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <p className="title">Задач пока нет</p>
          <p>Задачи появятся после запуска синхронизации или классификации</p>
        </div>
      ) : (
        <table className="table task-table">
          <thead>
            <tr>
              <th>Тип задачи</th>
              <th>Статус</th>
              <th>Канал</th>
              <th>Запущена</th>
              <th>Завершена</th>
              <th>Результат</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => {
              const r = t.result as Record<string, unknown> | null;
              return (
              <tr key={t.id}>
                <td>{formatTaskType(t.task_type)}</td>
                <td>
                  <span className={STATUS_CLASS[t.status] ?? 'badge badge-gray'}>
                    {STATUS_LABELS[t.status] ?? t.status}
                  </span>
                </td>
                <td>{t.channel_id != null ? `#${t.channel_id}` : '—'}</td>
                <td>{formatDate(t.started_at)}</td>
                <td>{formatDate(t.finished_at)}</td>
                <td>
                  {t.error ? (
                    <span className="task-error" title={t.error}>{t.error.length > 60 ? t.error.slice(0, 60) + '…' : t.error}</span>
                  ) : t.task_type === 'sync_channel' && r ? (
                    <div className="task-meta">
                      {r.scanned_video_ids != null && <span className="meta-item">Просканировано видео: {String(r.scanned_video_ids)}</span>}
                      {r.matched_candidates != null && <span className="meta-item">Подошло под фильтр: {String(r.matched_candidates)}</span>}
                      {r.skipped_by_filters != null && <span className="meta-item">Пропущено фильтрами: {String(r.skipped_by_filters)}</span>}
                      {r.stopped_reason != null && <span className="meta-item">Причина остановки: {stoppedReasonLabel(String(r.stopped_reason))}</span>}
                      {r.scores_calculated != null && <span className="meta-item">Скорингов рассчитано: {String(r.scores_calculated)}</span>}
                    </div>
                  ) : '—'}
                </td>
              </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
