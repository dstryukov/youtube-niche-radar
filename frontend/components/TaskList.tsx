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
              <th>Ошибка</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map(t => (
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
                <td>{t.error ? <span className="task-error" title={t.error}>{t.error.length > 60 ? t.error.slice(0, 60) + '…' : t.error}</span> : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
