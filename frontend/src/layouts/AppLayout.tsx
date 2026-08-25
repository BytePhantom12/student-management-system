import {BookOpen, CalendarCheck, ChevronDown, ClipboardList, GraduationCap, LayoutDashboard, LogOut, Menu, PanelLeftClose, PanelLeftOpen, ShieldCheck, UserCog, UserRound, UsersRound, X} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import {Link, NavLink, Outlet, useLocation} from 'react-router-dom';
import {useState} from 'react';
import {useAuth} from '../context/auth';
import {Avatar} from '../components/UI';
import BrandLogo from '../components/BrandLogo';
import ProtectedProfileImage from '../components/ProtectedProfileImage';

type NavItem = [string, string, LucideIcon];

export default function AppLayout() {
  const {user, logout} = useAuth();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar-collapsed') === 'true');
  const [accountOpen, setAccountOpen] = useState(false);
  const location = useLocation();
  const links: NavItem[] = [
    ['/dashboard', 'Dashboard', LayoutDashboard],
    ['/students', 'Students', GraduationCap],
    ['/hifz', 'Hifz Progress', BookOpen],
    ['/attendance', 'Attendance', CalendarCheck],
    ...(user?.is_admin ? [['/teachers', 'Teachers', UserRound] as NavItem] : []),
    ['/guardians', 'Parents / Guardians', UsersRound],
    ...(user?.is_admin ? [['/audit', 'Audit Logs', ClipboardList] as NavItem] : []),
  ];
  const superuserLinks: NavItem[] = [['/superuser', 'Overview', ShieldCheck], ['/superuser/users', 'Users', UserCog]];
  const fullName = `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || user?.username || 'Account';
  const section = [...superuserLinks, ...links].find(([to]) => location.pathname === to || location.pathname.startsWith(`${to}/`))?.[1] || 'Dashboard';

  function toggleCollapsed() {
    setCollapsed(value => {
      localStorage.setItem('sidebar-collapsed', String(!value));
      return !value;
    });
  }

  const renderLinks = (items: NavItem[]) => items.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === '/dashboard' || to === '/superuser'} onClick={() => setOpen(false)} title={collapsed ? label : undefined}><Icon size={19}/><span>{label}</span></NavLink>);

  return <div className={`shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <aside className={open ? 'open' : ''} aria-label="Primary navigation">
      <div className="brand"><Link className="brand-home" to="/dashboard" title="Halqatu Darul Taqwa" onClick={() => setOpen(false)}><BrandLogo decorative/><span className="brand-copy"><strong>Halqatu Darul Taqwa</strong><small>Student Management</small></span></Link><button className="icon-btn mobile-close" type="button" aria-label="Close navigation" onClick={() => setOpen(false)}><X size={20}/></button></div>
      <nav><span className="nav-section">Workspace</span>{renderLinks(links)}{user?.is_superuser && <><span className="nav-section">Superuser</span>{renderLinks(superuserLinks)}</>}</nav>
      <div className="sidebar-footer"><div className="sidebar-user"><Avatar name={fullName}/><span><strong>{fullName}</strong><small>{user?.is_superuser ? 'System superuser' : user?.role}</small></span></div><button className="logout icon-btn" type="button" aria-label="Sign out" title="Sign out" onClick={logout}><LogOut size={18}/></button></div>
    </aside>
    <main>
      <header className="topbar">
        <div className="topbar-leading"><button className="icon-btn menu" type="button" aria-label="Open navigation" onClick={() => setOpen(true)}><Menu size={20}/></button><BrandLogo size="small" className="mobile-header-logo"/><button className="icon-btn collapse-toggle" type="button" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} onClick={toggleCollapsed}>{collapsed ? <PanelLeftOpen size={19}/> : <PanelLeftClose size={19}/>}</button><div className="header-context"><small>Halqatu Darul Taqwa</small><strong>{section}</strong></div></div>
        <div className="account-menu"><button className="account-trigger" type="button" aria-expanded={accountOpen} onClick={() => setAccountOpen(value => !value)}>{user?.role === 'teacher' ? <ProtectedProfileImage endpoint="/teachers/me/profile-image/" hasImage={user.has_profile_image} name={fullName} size="sm"/> : <Avatar name={fullName} size="sm"/>}<span><strong>{fullName}</strong><small>{user?.is_superuser ? 'Superuser' : user?.role}</small></span><ChevronDown size={16}/></button>{accountOpen && <div className="account-dropdown"><div><strong>{fullName}</strong><small>{user?.email || user?.username}</small></div>{user?.role === 'teacher' && <Link to="/profile" onClick={() => setAccountOpen(false)}><UserRound size={17}/> My profile</Link>}<button type="button" onClick={logout}><LogOut size={17}/> Sign out</button></div>}</div>
      </header>
      <div className="content"><Outlet/></div>
    </main>
    {open && <button className="scrim" type="button" aria-label="Close navigation" onClick={() => setOpen(false)}/>}
  </div>;
}
