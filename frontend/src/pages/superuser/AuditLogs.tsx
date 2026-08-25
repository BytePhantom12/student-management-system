import {useEffect, useRef, useState} from 'react';
import {Search, ShieldAlert, X} from 'lucide-react';
import {useSearchParams} from 'react-router-dom';
import {api} from '../../services/api';
import {apiErrorMessage} from '../../utils/apiError';
import {Avatar, Badge, Button, Card, Empty, PageHeader, Skeleton} from '../../components/UI';
import Feedback from '../../components/Feedback';
import Pagination from '../../components/Pagination';
import type {AuditLog, Page} from '../../types';

const pageSize = 20;
function actionLabel(action: string) { return action.replace(/^(user|teacher_profile)_/, '').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
function category(action: string) { if (action.includes('delete') || action.includes('deactiv')) return 'delete'; if (action.includes('creat') || action.includes('activat')) return 'create'; if (action.includes('superuser') || action.includes('staff') || action.includes('password') || action.includes('role')) return 'security'; return 'update'; }
function metadataValue(value: unknown) { if (value === null || value === undefined) return '—'; if (typeof value === 'object') return JSON.stringify(value, null, 2); return String(value); }

export default function AuditLogs() {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<Page<AuditLog> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<AuditLog | null>(null);
  const query = params.toString();
  const page = Number(params.get('page') || 1);
  useEffect(() => { let active = true; api.get<Page<AuditLog>>(`/audit/?${query}`).then(response => {if (active) {setData(response.data); setError('');}}).catch(reason => {if (active) setError(apiErrorMessage(reason, 'Unable to load audit logs.'));}).finally(() => {if (active) setLoading(false);}); return () => {active = false;}; }, [query]);
  function setFilter(key: string, value: string) { setLoading(true); const next = new URLSearchParams(params); if (value) next.set(key, value); else next.delete(key); if (key !== 'page') next.delete('page'); setParams(next); }
  return <>
    <PageHeader eyebrow="Security & governance" title="Audit Logs" description="Monitor privileged user-management and domain activity across the system."/>
    <Card><div className="toolbar audit-filters"><label className="search"><Search size={17}/><input aria-label="Filter by action" placeholder="Filter by exact action" value={params.get('action') || ''} onChange={event => setFilter('action', event.target.value)}/></label><input aria-label="Filter by object type" placeholder="Object type, e.g. User" value={params.get('object_type') || ''} onChange={event => setFilter('object_type', event.target.value)}/>{query && <Button className="secondary" type="button" onClick={() => {setLoading(true); setParams({});}}>Clear filters</Button>}</div>{error && <Feedback tone="error" message={error}/>} {loading ? <Skeleton rows={7}/> : data?.results.length ? <><div className="table-wrap"><table><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Object</th><th>Details</th></tr></thead><tbody>{data.results.map(log => {const date = new Date(log.timestamp); const kind = category(log.action); const actor = log.user_name || 'System'; return <tr key={log.id}><td><span className="timestamp"><strong>{date.toLocaleDateString()}</strong><small>{date.toLocaleTimeString()}</small></span></td><td><div className="actor-cell"><Avatar name={actor} size="sm"/><span><strong>{actor}</strong><small>{log.user_name ? 'Authenticated actor' : 'System / unavailable'}</small></span></div></td><td><span className={`audit-action ${kind}`}><i/><span>{actionLabel(log.action)}</span><Badge tone={kind}>{kind}</Badge></span></td><td><strong>{log.object_type} #{log.object_id || '—'}</strong></td><td><Button type="button" className="secondary compact" onClick={() => setSelected(log)}>View details</Button></td></tr>;})}</tbody></table></div><Pagination page={page} total={data.count} pageSize={pageSize} hasPrevious={Boolean(data.previous)} hasNext={Boolean(data.next)} onPage={value => setFilter('page', String(value))}/></> : <Empty icon={ShieldAlert} text="No audit activity found" description="Try adjusting the current action or object filters."/>}</Card>
    <AuditDetails log={selected} onClose={() => setSelected(null)}/>
  </>;
}

function AuditDetails({log, onClose}: {log: AuditLog | null; onClose: () => void}) {
  const dialogRef = useRef<HTMLElement>(null);
  useEffect(() => { if (!log) return; const previous = document.activeElement as HTMLElement | null; const frame = requestAnimationFrame(() => dialogRef.current?.querySelector<HTMLButtonElement>('button')?.focus()); const keys = (event: KeyboardEvent) => {if (event.key === 'Escape') onClose(); if (event.key !== 'Tab' || !dialogRef.current) return; const controls = [...dialogRef.current.querySelectorAll<HTMLElement>('button:not(:disabled), [href]')]; if (!controls.length) return; const first = controls[0]; const last = controls[controls.length - 1]; if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last.focus();} else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}}; document.addEventListener('keydown', keys); return () => {cancelAnimationFrame(frame); document.removeEventListener('keydown', keys); previous?.focus();}; }, [log, onClose]);
  if (!log) return null;
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => {if (event.target === event.currentTarget) onClose();}}><section ref={dialogRef} className="details-dialog" role="dialog" aria-modal="true" aria-labelledby="activity-title"><div className="page-title"><div><span className="eyebrow">Audit record</span><h2 id="activity-title">Activity Details</h2></div><button className="icon-btn" type="button" aria-label="Close details" onClick={onClose}><X size={18}/></button></div><dl className="metadata-grid"><div><dt>Action</dt><dd>{actionLabel(log.action)}</dd></div><div><dt>Actor</dt><dd>{log.user_name || 'System / unavailable'}</dd></div><div><dt>Object</dt><dd>{log.object_type} #{log.object_id || '—'}</dd></div><div><dt>Timestamp</dt><dd>{new Date(log.timestamp).toLocaleString()}</dd></div>{Object.entries(log.metadata || {}).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd><pre>{metadataValue(value)}</pre></dd></div>)}</dl><div className="actions"><Button className="secondary" type="button" onClick={onClose}>Close</Button></div></section></div>;
}
