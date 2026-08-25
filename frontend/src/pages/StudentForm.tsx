import {useEffect, useState} from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import {Button, Card, Input, Select} from '../components/UI';
import {useAuth} from '../context/auth';
import type {Guardian, Page, Student, Teacher} from '../types';

const blank = {student_id: '', first_name: '', last_name: '', gender: 'male', date_of_birth: '', phone: '', email: '', address: '', guardian_name: '', guardian_phone: '', guardian_relationship: '', enrollment_date: new Date().toISOString().slice(0, 10), status: 'active', assigned_teacher: null, primary_guardian: null, notes: ''};

export default function StudentForm() {
  const {id} = useParams();
  const navigate = useNavigate();
  const {user} = useAuth();
  const [form, setForm] = useState<Record<string, unknown>>(blank);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const requests: Promise<void>[] = [
      api.get<Page<Guardian>>('/guardians/?is_active=true').then(response => { if (active) setGuardians(response.data.results); }),
    ];
    if (id) requests.push(api.get<Student>(`/students/${id}/`).then(response => { if (active) setForm(response.data as unknown as Record<string, unknown>); }));
    if (user?.is_admin) requests.push(api.get<Page<Teacher>>('/teachers/?is_active=true').then(response => { if (active) setTeachers(response.data.results); }));
    Promise.all(requests).catch(reason => { if (active) setError(apiErrorMessage(reason, 'Unable to load student form options.')); });
    return () => { active = false; };
  }, [id, user?.is_admin]);

  function change(key: string, value: unknown) {
    setForm(current => ({...current, [key]: value}));
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setError('');
    try {
      const response = id ? await api.patch(`/students/${id}/`, form) : await api.post('/students/', form);
      navigate(`/students/${response.data.id}`);
    } catch (reason) {
      setError(apiErrorMessage(reason, 'Unable to save student.'));
    }
  }

  return <>
    <div className="page-title"><div><h1>{id ? 'Edit' : 'Add'} student</h1><p>Assign existing teacher and guardian records.</p></div></div>
    <Card><form onSubmit={save}>
      {error && <div className="alert" role="alert">{error}</div>}
      <div className="form-grid">
        <Input label="Student ID" required value={String(form.student_id || '')} onChange={event => change('student_id', event.target.value)}/>
        <Input label="First name" required value={String(form.first_name || '')} onChange={event => change('first_name', event.target.value)}/>
        <Input label="Last name" required value={String(form.last_name || '')} onChange={event => change('last_name', event.target.value)}/>
        <Select label="Gender" value={String(form.gender)} onChange={event => change('gender', event.target.value)}><option value="male">Male</option><option value="female">Female</option></Select>
        <Input label="Date of birth" type="date" required value={String(form.date_of_birth || '')} onChange={event => change('date_of_birth', event.target.value)}/>
        <Input label="Enrollment date" type="date" required value={String(form.enrollment_date || '')} onChange={event => change('enrollment_date', event.target.value)}/>
        <Input label="Phone" value={String(form.phone || '')} onChange={event => change('phone', event.target.value)}/>
        <Input label="Email" type="email" value={String(form.email || '')} onChange={event => change('email', event.target.value)}/>
        {user?.is_admin && <Select label="Dedicated teacher" value={String(form.assigned_teacher ?? '')} onChange={event => change('assigned_teacher', event.target.value ? Number(event.target.value) : null)}><option value="">Unassigned</option>{teachers.map(teacher => <option key={teacher.id} value={teacher.id}>{teacher.first_name} {teacher.last_name}</option>)}</Select>}
        <Select label="Primary parent / guardian" required value={String(form.primary_guardian ?? '')} onChange={event => change('primary_guardian', event.target.value ? Number(event.target.value) : null)}><option value="">Select a guardian</option>{guardians.map(guardian => <option key={guardian.id} value={guardian.id}>{guardian.name} — {guardian.phone}</option>)}</Select>
        <Input label="Guardian relationship" required value={String(form.guardian_relationship || '')} onChange={event => change('guardian_relationship', event.target.value)}/>
      </div>
      <div className="actions"><Button type="button" className="secondary" onClick={() => navigate(-1)}>Cancel</Button><Button>Save student</Button></div>
    </form></Card>
  </>;
}
