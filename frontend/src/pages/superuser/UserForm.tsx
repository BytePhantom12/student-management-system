import {useEffect, useState} from 'react';
import {useNavigate, useParams} from 'react-router-dom';
import {api} from '../../services/api';
import {apiErrorMessage} from '../../utils/apiError';
import {Button, Card, Input, PageHeader, Select, Skeleton} from '../../components/UI';
import Feedback from '../../components/Feedback';
import type {ManagedUser} from '../../types';

type FormState = {username: string; first_name: string; last_name: string; email: string; role: 'admin' | 'teacher'; is_active: boolean; is_staff: boolean; is_superuser: boolean; teacher_phone: string; password: string; password_confirm: string};
const initial: FormState = {username: '', first_name: '', last_name: '', email: '', role: 'teacher', is_active: true, is_staff: false, is_superuser: false, teacher_phone: '', password: '', password_confirm: ''};

export default function UserForm() {
  const {id} = useParams();
  const navigate = useNavigate();
  const editing = Boolean(id);
  const [form, setForm] = useState<FormState>(initial);
  const [loading, setLoading] = useState(editing);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { if (!id) return; api.get<ManagedUser>(`/users/${id}/`).then(response => {const user = response.data; setForm(current => ({...current, username: user.username, first_name: user.first_name, last_name: user.last_name, email: user.email}));}).catch(reason => setError(apiErrorMessage(reason, 'Unable to load this user.'))).finally(() => setLoading(false)); }, [id]);
  function change<K extends keyof FormState>(key: K, value: FormState[K]) {setForm(current => ({...current, [key]: value}));}
  async function submit(event: React.FormEvent) {event.preventDefault(); if (busy) return; setBusy(true); setError(''); try {if (editing) {await api.patch(`/users/${id}/`, {username: form.username, first_name: form.first_name, last_name: form.last_name, email: form.email}); navigate(`/superuser/users/${id}`, {state: {message: 'User information updated.'}});} else {const payload = {username: form.username, first_name: form.first_name, last_name: form.last_name, email: form.email, role: form.role, is_active: form.is_active, is_staff: form.is_staff, is_superuser: form.is_superuser, teacher_phone: form.role === 'teacher' ? form.teacher_phone : '', password: form.password, password_confirm: form.password_confirm}; const response = await api.post<ManagedUser>('/users/', payload); navigate(`/superuser/users/${response.data.id}`, {state: {message: 'User created successfully.'}});}} catch (reason) {setError(apiErrorMessage(reason, editing ? 'Unable to update this user.' : 'Unable to create this user.'));} finally {setBusy(false);}}
  if (loading) return <Skeleton rows={5}/>;
  if (editing && error && !form.username) return <Feedback tone="error" message={error}/>;
  return <>
    <PageHeader eyebrow="Account management" title={editing ? 'Edit User' : 'Create User'} description={editing ? 'Update core identity and contact information for this account.' : 'Create an application administrator, teacher, or system superuser.'}/>
    {error && <Feedback tone="error" message={error}/>}<Card className="form-card"><form onSubmit={submit}>
      <section className="form-section"><div className="section-heading"><h2>Basic information</h2><p>Identity and contact details shown throughout the platform.</p></div><div className="form-grid"><Input label="Username" required value={form.username} onChange={event => change('username', event.target.value)}/><Input label="Email address" type="email" value={form.email} onChange={event => change('email', event.target.value)}/><Input label="First name" value={form.first_name} onChange={event => change('first_name', event.target.value)}/><Input label="Last name" value={form.last_name} onChange={event => change('last_name', event.target.value)}/></div></section>
      {!editing && <><section className="form-section"><div className="section-heading"><h2>Account access</h2><p>Choose the application role and initial credentials.</p></div><div className="form-grid"><Select label="Application role" hint="Controls normal application behavior." value={form.role} onChange={event => change('role', event.target.value as FormState['role'])}><option value="teacher">Teacher</option><option value="admin">Application Admin</option></Select>{form.role === 'teacher' && <Input label="Teacher phone" value={form.teacher_phone} onChange={event => change('teacher_phone', event.target.value)}/>}<Input label="Password" type="password" required autoComplete="new-password" value={form.password} onChange={event => change('password', event.target.value)}/><Input label="Confirm password" type="password" required autoComplete="new-password" value={form.password_confirm} onChange={event => change('password_confirm', event.target.value)}/></div></section><section className="form-section"><div className="section-heading"><h2>Privileges</h2><p>These settings are independent and should be granted deliberately.</p></div><div className="privilege-options"><label><input type="checkbox" checked={form.is_active} onChange={event => change('is_active', event.target.checked)}/><span><strong>Active account</strong><small>User can authenticate immediately.</small></span></label><label><input type="checkbox" checked={form.is_staff} onChange={event => change('is_staff', event.target.checked)}/><span><strong>Django Admin Staff Access</strong><small>Allows access to Django `/admin/`; separate from Application Role.</small></span></label><label className={form.is_superuser ? 'critical-option' : ''}><input type="checkbox" checked={form.is_superuser} onChange={event => change('is_superuser', event.target.checked)}/><span><strong>System Superuser</strong><small>Grants full system-level administrative privileges.</small></span></label></div></section></>}
      <div className="form-note">{editing ? 'Role, activation, staff access, superuser status, and passwords remain protected by dedicated actions on the user detail page.' : 'Application Role, Django Staff Access, and System Superuser are separate capabilities.'}</div><div className="actions"><Button type="button" className="secondary" disabled={busy} onClick={() => navigate(-1)}>Cancel</Button><Button disabled={busy}>{busy ? 'Saving…' : editing ? 'Save changes' : 'Create user'}</Button></div>
    </form></Card>
  </>;
}
