import {useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {BookOpen, CalendarCheck, Edit} from 'lucide-react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import type {Student} from '../types';
import {Avatar, Badge, Card, PageHeader, Skeleton} from '../components/UI';

export default function StudentProfile() {
  const {id} = useParams();
  const [student, setStudent] = useState<Student | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {let active = true; api.get<Student>(`/students/${id}/`).then(response => {if (active) setStudent(response.data);}).catch(reason => {if (active) setError(apiErrorMessage(reason, 'Unable to load this student.'));}); return () => {active = false;};}, [id]);
  if (!student) return error ? <div className="alert" role="alert">{error}</div> : <Skeleton rows={5}/>;
  return <><PageHeader eyebrow="Student records" title="Student Profile" description="Review personal details, family contact, and learning records." actions={<Link className="btn" to={`/students/${id}/edit`}><Edit size={17}/> Edit student</Link>}/><div className="profile-hero"><Avatar name={student.full_name} size="lg"/><div><h1>{student.full_name}</h1><p>{student.student_id} · {student.gender}</p></div><span className="profile-status"><Badge tone={student.status}>{student.status}</Badge></span></div><div className="profile-grid"><Card><h2>Personal information</h2><dl><dt>Date of birth</dt><dd>{student.date_of_birth}</dd><dt>Gender</dt><dd>{student.gender}</dd><dt>Phone</dt><dd>{student.phone || '—'}</dd><dt>Email</dt><dd>{student.email || '—'}</dd><dt>Dedicated teacher</dt><dd>{student.teacher?.name || 'Unassigned'}</dd></dl></Card><Card><h2>Primary parent / guardian</h2><dl><dt>Name</dt><dd>{student.parent?.name || 'Unassigned'}</dd><dt>Relationship</dt><dd>{student.guardian_relationship}</dd><dt>Phone</dt><dd>{student.parent?.phone || '—'}</dd><dt>Email</dt><dd>{student.parent?.email || '—'}</dd></dl></Card><Card className="wide"><h2>Learning record</h2><div className="quick-links"><Link to={`/hifz?student=${id}`}><BookOpen size={18}/>Hifz progress</Link><Link to={`/attendance?student=${id}`}><CalendarCheck size={18}/>Attendance history</Link></div></Card></div></>;
}
