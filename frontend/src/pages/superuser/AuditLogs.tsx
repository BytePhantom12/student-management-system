import {useEffect, useState} from 'react';
import {useSearchParams} from 'react-router-dom';
import {api} from '../../services/api';
import {apiErrorMessage} from '../../utils/apiError';
import {Button, Card, Empty, Spinner} from '../../components/UI';
import Feedback from '../../components/Feedback';
import Pagination from '../../components/Pagination';
import type {AuditLog, Page} from '../../types';

const pageSize = 20;
function actionLabel(action: string) { return action.replace(/^(user|teacher_profile)_/, '').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
function metadataValue(value: unknown) { if (value === null || value === undefined) return '—'; if (typeof value === 'object') return JSON.stringify(value, null, 2); return String(value); }

export default function AuditLogs() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<Page<AuditLog> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);
  const query = params.toString();
  const page = Number(params.get('page') || 1);

  useEffect(() => {
    let active = true;
    api.get<Page<AuditLog>>(`/audit/?${query}`)
      .then(response => { if (active) { setData(response.data); setError(''); } })
      .catch(reason => { if (active) setError(apiErrorMessage(reason, 'Unable to load audit logs.')); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);

  function setFilter(key: string, value: string) {
    setLoading(true);
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== 'page') next.delete('page');
    setParams(next);
  }

  return <><div className="page-title"><div><h1>Audit Logs</h1><p>Review privileged user-management and domain activity.</p></div></div><Card><div className="toolbar audit-filters"><input aria-label="Filter by action" placeholder="Exact action, e.g. user_created" value={params.get('action') || ''} onChange={event => setFilter('action', event.target.value)}/><input aria-label="Filter by object type" placeholder="Object type, e.g. User" value={params.get('object_type') || ''} onChange={event => setFilter('object_type', event.target.value)}/></div>{error && <Feedback tone="error" message={error}/>} {loading ? <Spinner/> : data?.results.length ? <><div className="table-wrap"><table><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Object</th><th>Metadata</th></tr></thead><tbody>{data.results.map(log => <AuditRow key={log.id} log={log} expanded={expanded === log.id} onToggle={() => setExpanded(value => value === log.id ? null : log.id)}/>)}</tbody></table></div><Pagination page={page} total={data.count} pageSize={pageSize} hasPrevious={Boolean(data.previous)} hasNext={Boolean(data.next)} onPage={value => setFilter('page', String(value))}/></> : <Empty text="No audit records found."/>}</Card></>;
}

function AuditRow({log, expanded, onToggle}: {log: AuditLog; expanded: boolean; onToggle: () => void}) {
  return <><tr><td>{new Date(log.timestamp).toLocaleString()}</td><td>{log.user_name || 'System / unavailable'}</td><td>{actionLabel(log.action)}</td><td>{log.object_type} #{log.object_id || '—'}</td><td><Button type="button" className="secondary compact" onClick={onToggle} aria-expanded={expanded}>{expanded ? 'Hide details' : 'View details'}</Button></td></tr>{expanded && <tr className="metadata-row"><td colSpan={5}>{Object.keys(log.metadata || {}).length ? <dl>{Object.entries(log.metadata).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd><pre>{metadataValue(value)}</pre></dd></div>)}</dl> : <span className="muted">No metadata recorded.</span>}</td></tr>}</>;
}
