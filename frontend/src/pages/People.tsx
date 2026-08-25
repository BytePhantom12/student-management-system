import {useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import {Card, Empty, Spinner} from '../components/UI';
import type {Guardian, Page, Teacher} from '../types';

type Kind = 'teachers' | 'guardians';

export function PeopleList({kind}: {kind: Kind}) {
  const [rows, setRows] = useState<(Teacher | Guardian)[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api.get<Page<Teacher | Guardian>>(`/${kind}/`)
      .then(response => { if (active) setRows(response.data.results); })
      .catch(reason => { if (active) { setError(apiErrorMessage(reason, 'Unable to load records.')); setRows([]); } });
    return () => { active = false; };
  }, [kind]);
  return <><div className="page-title"><div><h1>{kind === 'teachers' ? 'Teachers' : 'Parents / Guardians'}</h1><p>Select a record to view its assigned students.</p></div></div><Card>{error && <div className="alert" role="alert">{error}</div>}{!rows ? <Spinner/> : !rows.length ? <Empty text="No records available."/> : <div className="table-wrap"><table><thead><tr><th>Name</th><th>Contact</th><th>Students</th><th>Status</th></tr></thead><tbody>{rows.map(row => {const name = 'name' in row ? row.name : `${row.first_name} ${row.last_name}`; return <tr key={row.id}><td><Link to={`/${kind}/${row.id}`}><strong>{name}</strong></Link></td><td>{row.phone || row.email || '—'}</td><td>{row.student_count}</td><td>{row.is_active ? 'Active' : 'Inactive'}</td></tr>;})}</tbody></table></div>}</Card></>;
}

export function PeopleProfile({kind}: {kind: Kind}) {
  const {id} = useParams();
  const [row, setRow] = useState<Teacher | Guardian | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api.get<Teacher | Guardian>(`/${kind}/${id}/`)
      .then(response => { if (active) setRow(response.data); })
      .catch(reason => { if (active) setError(apiErrorMessage(reason, 'Unable to load this record.')); });
    return () => { active = false; };
  }, [id, kind]);
  if (!row) return error ? <div className="alert" role="alert">{error}</div> : <Spinner/>;
  const name = 'name' in row ? row.name : `${row.first_name} ${row.last_name}`;
  return <><div className="page-title"><div><h1>{name}</h1><p>{kind === 'teachers' ? 'Teacher' : 'Parent / guardian'} · {row.phone || row.email || 'No contact details'}</p></div></div><Card><h2>Associated students</h2>{row.students.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>ID</th></tr></thead><tbody>{row.students.map(student => <tr key={student.id}><td><Link to={`/students/${student.id}`}>{student.name}</Link></td><td>{student.student_id}</td></tr>)}</tbody></table></div> : <Empty text="No students assigned."/>}</Card></>;
}
