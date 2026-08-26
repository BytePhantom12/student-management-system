import {useState} from 'react';
import {Navigate, useLocation} from 'react-router-dom';
import {BookOpen, Eye, EyeOff, LockKeyhole, LogIn, UserRound} from 'lucide-react';
import {useAuth} from '../context/auth';
import BrandLogo from '../components/BrandLogo';

function GeometricCorner({className}: {className: string}) {
  return <svg className={`login-geometry ${className}`} viewBox="0 0 240 240" aria-hidden="true">
    <defs><pattern id={`geometry-${className}`} width="54" height="54" patternUnits="userSpaceOnUse"><path d="M27 1 38 16l15 11-15 11-11 15-11-15L1 27l15-11Z"/><path d="M27 10 35 19l9 8-9 8-8 9-8-9-9-8 9-8Z"/><circle cx="27" cy="27" r="4"/></pattern></defs>
    <rect width="240" height="240" fill={`url(#geometry-${className})`}/>
  </svg>;
}

function MosqueScene() {
  return <svg className="login-mosque" viewBox="0 0 760 360" preserveAspectRatio="none" aria-hidden="true">
    <g className="mosque-far"><path d="M0 296h760v64H0z"/><path d="M78 296v-84h18v84m-9-111-13 27h26zM632 296v-112h16v112m-8-140-13 28h26z"/><path d="M142 296v-58h78v58m-39-102c-31 15-39 44-39 44h78s-8-29-39-44zm214 102v-75h102v75m-51-130c-42 20-51 55-51 55h102s-9-35-51-55z"/></g>
    <g className="mosque-near"><path d="M236 310v-112h28v112m-14-160-19 48h38zM250 131v19"/><path d="M275 310v-70h176v70m-88-159c-62 30-75 89-75 89h150s-13-59-75-89zM356 127h14v27h-14zM363 109v18"/><path d="M463 310v-143h25v143m-13-189-17 46h34zM475 105v16"/><path d="M196 310v-60h55v60m-28-95c-23 11-28 35-28 35h56s-5-24-28-35zm289 95v-67h65v67m-32-110c-27 13-33 43-33 43h66s-6-30-33-43z"/></g>
    <path className="mosque-ground" d="M0 309c104-28 182 14 286-4 122-21 208-10 303 7 65 12 116 5 171-8v56H0z"/>
  </svg>;
}

function FlowingWaves() {
  return <svg className="login-waves" viewBox="0 0 820 270" preserveAspectRatio="none" aria-hidden="true">
    <path className="wave-cream" d="M0 72c178 94 332 97 485 26C629 31 704 5 820 19v251H0Z"/>
    <path className="wave-gold" d="M0 113c175 78 333 73 492-3 137-65 235-83 328-67v9c-100-14-195 7-324 72-164 82-329 85-496 2Z"/>
    <path className="wave-sage" d="M0 137c190 91 343 79 496 1 132-68 233-80 324-60v27c-94-17-188-2-314 67-160 87-329 102-506 8Z"/>
    <path className="wave-white" d="M0 168c171 78 337 83 505 9 129-57 229-68 315-50v143H0Z"/>
  </svg>;
}

export default function Login() {
  const {user, login} = useAuth();
  const rememberedUsername = localStorage.getItem('remembered-username') || '';
  const [username, setUsername] = useState(rememberedUsername);
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(Boolean(rememberedUsername));
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const location = useLocation();

  if (user) return <Navigate to={(location.state as {from?: string})?.from || '/dashboard'}/>;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await login(username, password);
      if (remember) localStorage.setItem('remembered-username', username);
      else localStorage.removeItem('remembered-username');
    }
    catch { setError('Invalid username or password.'); }
    finally { setBusy(false); }
  }

  return <main className="login login-v2"><div className="login-shell">
    <section className="login-brand" aria-label="Halqatu Darul Taqwa">
      <GeometricCorner className="geometry-top-left"/>
      <MosqueScene/>
      <FlowingWaves/>
      <BrandLogo size="large"/>
      <div className="brand-quote"><div className="quote-ornament"><span/><i/><BookOpen size={30}/><i/><span/></div><blockquote>&ldquo;By knowledge we build, and by character we shine&rdquo;</blockquote><div className="quote-rule"><span/></div></div>
      <svg className="curved-divider" viewBox="0 0 150 900" preserveAspectRatio="none" aria-hidden="true"><path className="divider-shadow" d="M132-20C26 128 15 275 82 428c63 145 52 304-48 492"/><path className="divider-gold" d="M121-20C16 128 6 275 72 428c62 145 51 304-49 492"/></svg>
    </section>
    <section className="login-side">
      <GeometricCorner className="geometry-bottom-right"/>
      <div className="login-panel">
        <span>STUDENT MANAGEMENT SYSTEM</span>
        <h1><strong>Welcome</strong> <em>Back</em></h1>
        <p>Sign in with your credentials to continue</p>
        <form onSubmit={submit}>
          {error && <div className="alert" role="alert">{error}</div>}
          <label className="login-field"><span>Username</span><div><UserRound size={18}/><input aria-label="Username" autoComplete="username" placeholder="Enter your username" value={username} onChange={event => setUsername(event.target.value)} required autoFocus/></div></label>
          <label className="login-field"><span>Password</span><div><LockKeyhole size={18}/><input aria-label="Password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Enter your password" value={password} onChange={event => setPassword(event.target.value)} required/><button type="button" className="password-toggle" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}>{showPassword ? <Eye size={19}/> : <EyeOff size={19}/>}</button></div></label>
          <label className="remember-me"><input type="checkbox" checked={remember} onChange={event => setRemember(event.target.checked)}/><span>Remember me</span></label>
          <button className="login-submit" disabled={busy}><LogIn size={18}/>{busy ? 'Signing in...' : 'Sign In'}</button>
        </form>
        <footer><div className="footer-divider"><span/></div><p>&copy; 2026 Darul Taqwa Student Management System.<br/>All rights reserved.</p></footer>
      </div>
    </section>
  </div></main>;
}
