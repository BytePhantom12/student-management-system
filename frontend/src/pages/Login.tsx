import {useState} from 'react';
import {Navigate, useLocation} from 'react-router-dom';
import {useAuth} from '../context/auth';
import {Button, Input} from '../components/UI';
import BrandLogo from '../components/BrandLogo';

export default function Login() {
  const {user, login} = useAuth(); const [username, setUsername] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const location = useLocation();
  if (user) return <Navigate to={(location.state as {from?: string})?.from || '/dashboard'}/>;
  async function submit(event: React.FormEvent) {event.preventDefault(); setBusy(true); setError(''); try {await login(username, password);} catch {setError('Invalid username or password.');} finally {setBusy(false);}}
  return <main className="login"><div className="login-shell"><section className="login-brand"><BrandLogo size="large"/><div><h1>Halqatu Darul Taqwa</h1><strong>Student Management</strong><p>Manage students, learning, attendance and administration in one focused platform.</p></div></section><section className="login-panel"><span>Student management</span><h2>Welcome back</h2><p>Sign in with your authorized institution account.</p><form onSubmit={submit}>{error && <div className="alert" role="alert">{error}</div>}<Input label="Username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required autoFocus/><Input label="Password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required/><Button disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button></form></section></div></main>;
}
