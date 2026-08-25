import {useEffect, useState} from 'react';
import {Link, useSearchParams} from 'react-router-dom';
import {Plus, Search} from 'lucide-react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import type {Page, Student} from '../types';
import {Badge, Button, Card, Empty, Spinner} from '../components/UI';

export default function Students() {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState<Page<Student> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const query = params.toString();

  useEffect(() => {
    let active = true;
    api.get<Page<Student>>(`/students/?${query}`)
      .then(response => { if (active) { setPage(response.data); setError(''); } })
      .catch(reason => { if (active) setError(apiErrorMessage(reason, 'Unable to load students.')); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);

  function set(key: string, value: string) {
    setLoading(true);
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== 'page') next.delete('page');
    setParams(next);
  }

  return <>
    <div className="page-title"><div><h1>Students</h1><p>Manage enrolment, assignments and student records.</p></div><Link className="btn" to="/students/new"><Plus size={18}/> Add student</Link></div>
    <Card>
      <div className="toolbar"><label className="search"><Search size={18}/><input aria-label="Search students" placeholder="Search students…" defaultValue={params.get('search') || ''} onKeyDown={event => { if (event.key === 'Enter') set('search', event.currentTarget.value); }}/></label><select aria-label="Student status" value={params.get('status') || ''} onChange={event => set('status', event.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select><select aria-label="Student gender" value={params.get('gender') || ''} onChange={event => set('gender', event.target.value)}><option value="">All genders</option><option value="male">Male</option><option value="female">Female</option></select></div>
      {error && <div className="alert" role="alert">{error}</div>}
      {loading ? <Spinner/> : page?.results.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>ID</th><th>Teacher</th><th>Contact</th><th>Status</th></tr></thead><tbody>{page.results.map(student => <tr key={student.id}><td><Link to={`/students/${student.id}`}><strong>{student.full_name}</strong></Link></td><td>{student.student_id}</td><td>{student.teacher_name || 'Unassigned'}</td><td>{student.phone || student.email || '—'}</td><td><Badge tone={student.status}>{student.status}</Badge></td></tr>)}</tbody></table></div> : <Empty text="No students match these filters."/>}
      <div className="pagination"><Button disabled={!page?.previous} onClick={() => set('page', String(Math.max(1, Number(params.get('page') || 1) - 1)))}>Previous</Button><span>{page?.count || 0} students</span><Button disabled={!page?.next} onClick={() => set('page', String(Number(params.get('page') || 1) + 1))}>Next</Button></div>
    </Card>
  </>;
}
