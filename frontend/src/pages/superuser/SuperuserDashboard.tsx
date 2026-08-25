import {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {Plus, ShieldCheck, UserCheck, UserCog, UserMinus, Users} from 'lucide-react';
import {api} from '../../services/api';
import {apiErrorMessage} from '../../utils/apiError';
import {Avatar, Badge, Card, Empty, PageHeader, Skeleton, StatCard} from '../../components/UI';
import Feedback from '../../components/Feedback';
import type {SuperuserDashboardData} from '../../types';

export default function SuperuserDashboard() {
  const [data, setData] = useState<SuperuserDashboardData | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { api.get<SuperuserDashboardData>('/users/dashboard/').then(response => setData(response.data)).catch(reason => setError(apiErrorMessage(reason, 'Unable to load the superuser dashboard.'))); }, []);
  if (error && !data) return <Feedback tone="error" message={error}/>;
  if (!data) return <><PageHeader eyebrow="System administration" title="Superuser overview" description="Loading account and privilege metrics."/><Skeleton rows={8} cards/></>;
  return <>
    <PageHeader eyebrow="System administration" title="Superuser Overview" description="Monitor accounts, privileges, and active teacher profiles across the platform." actions={<Link className="btn" to="/superuser/users/new"><Plus size={17}/> Create user</Link>}/>
    <div className="stats superuser-stats"><StatCard label="Total users" value={data.total_users} icon={Users} supporting={`${data.active_users} active accounts`}/><StatCard label="Active accounts" value={data.active_users} icon={UserCheck} supporting="Can currently authenticate"/><StatCard label="Teacher accounts" value={data.teacher_role_accounts} icon={UserCog} tone="blue" supporting={`${data.active_teacher_profiles} active profiles`}/><StatCard label="Application admins" value={data.application_admin_accounts} icon={ShieldCheck} tone="gold" supporting="Application-level access"/></div>
    <div className="stats superuser-stats"><StatCard secondary label="Inactive accounts" value={data.inactive_users} icon={UserMinus} tone="red"/><StatCard secondary label="Django staff" value={data.staff_accounts} icon={UserCog} tone="gold"/><StatCard secondary label="System superusers" value={data.superusers} icon={ShieldCheck}/><StatCard secondary label="Teacher profiles" value={data.active_teacher_profiles} icon={UserCheck} tone="blue"/></div>
    <Card><h2>Recently created users</h2>{data.recent_users.length ? <div className="table-wrap"><table><thead><tr><th>User</th><th>Username</th><th>Application role</th><th>Status</th><th>Date joined</th></tr></thead><tbody>{data.recent_users.map(user => {const name = `${user.first_name} ${user.last_name}`.trim() || user.username; return <tr key={user.id}><td><div className="actor-cell"><Avatar name={name} size="sm"/><span><Link to={`/superuser/users/${user.id}`}><strong>{name}</strong></Link><small>{user.email || 'No email'}</small></span></div></td><td>@{user.username}</td><td><Badge tone={user.role}>{user.role}</Badge></td><td><Badge tone={user.is_active ? 'active' : 'inactive'}>{user.is_active ? 'Active' : 'Inactive'}</Badge></td><td>{new Date(user.date_joined).toLocaleDateString()}</td></tr>;})}</tbody></table></div> : <Empty text="No users created yet" description="Create the first managed account to see it here." action={<Link className="btn" to="/superuser/users/new">Create user</Link>}/>}</Card>
  </>;
}
