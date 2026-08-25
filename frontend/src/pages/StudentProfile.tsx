import {useEffect, useState} from 'react';
import {Link, useParams} from 'react-router-dom';
import {BookOpen, CalendarCheck, Edit} from 'lucide-react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import type {Student} from '../types';
import {Badge, Card, Spinner} from '../components/UI';

export default function StudentProfile() {
  const {id} = useParams();
  const [student, setStudent] = useState<Student | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api.get<Student>(`/students/${id}/`)
      .then(response => { if (active) setStudent(response.data); })
      .catch(reason => { if (active) setError(apiErrorMessage(reason, 'Unable to load this student.')); });
    return () => { active = false; };
  }, [id]);
  if (!student) return error ? <div className="alert" role="alert">{error}</div> : <Spinner/>;
  return <><div className="page-title"><div><h1>{student.full_name}</h1><p>{student.student_id} · <Badge tone={student.status}>{student.status}</Badge></p></div><Link className="btn" to={`/students/${id}/edit`}><Edit size={17}/> Edit</Link></div><div className="profile-grid"><Card><h2>Personal information</h2><dl><dt>Date of birth</dt><dd>{student.date_of_birth}</dd><dt>Gender</dt><dd>{student.gender}</dd><dt>Phone</dt><dd>{student.phone || '—'}</dd><dt>Email</dt><dd>{student.email || '—'}</dd><dt>Assigned teacher</dt><dd>{student.teacher?.name || 'Unassigned'}</dd></dl></Card><Card><h2>Primary parent / guardian</h2><dl><dt>Name</dt><dd>{student.parent?.name || 'Unassigned'}</dd><dt>Relationship</dt><dd>{student.guardian_relationship}</dd><dt>Phone</dt><dd>{student.parent?.phone || '—'}</dd><dt>Email</dt><dd>{student.parent?.email || '—'}</dd></dl></Card><Card className="wide"><h2>Learning record</h2><div className="quick-links"><Link to={`/hifz?student=${id}`}><BookOpen/>Hifz progress</Link><Link to={`/attendance?student=${id}`}><CalendarCheck/>Attendance history</Link></div></Card></div></>;
}
