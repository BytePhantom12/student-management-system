import {useEffect, useState, type CSSProperties} from 'react';
import {GraduationCap, UserCheck, UserX, Users} from 'lucide-react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import {useAuth} from '../context/auth';
import {Card, Empty, PageHeader, Skeleton, StatCard} from '../components/UI';
import Feedback from '../components/Feedback';

type Data = {students: {total: number; active: number; inactive: number}; teachers?: number; attendance_percentage: number; today_attendance: Record<string, number>; recent_hifz: {id: number; student__first_name: string; student__last_name: string; surah: number; progress_percentage: number; status: string}[]};

export default function Dashboard() {
  const {user} = useAuth();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { api.get<Data>(`/dashboard/${user?.is_admin ? 'admin' : 'teacher'}/`).then(response => setData(response.data)).catch(reason => setError(apiErrorMessage(reason, 'Unable to load the dashboard.'))); }, [user]);
  if (error && !data) return <Feedback tone="error" message={error}/>;
  if (!data) return <><PageHeader eyebrow="Institution overview" title="Dashboard" description="Loading your latest student and learning information."/><Skeleton rows={4} cards/></>;
  const attendanceStyle = {'--attendance': `${Math.min(100, data.attendance_percentage)}%`} as CSSProperties;
  return <>
    <PageHeader eyebrow="Institution overview" title={<>Assalamu alaikum, {user?.first_name || user?.username}</>} description="A clear view of today’s students, attendance, and recent learning activity."/>
    <div className="stats"><StatCard label="Total students" value={data.students.total} icon={Users} supporting={`${data.students.active} currently active`}/><StatCard label="Active students" value={data.students.active} icon={UserCheck} tone="emerald" supporting="Available in current records"/><StatCard label="Inactive students" value={data.students.inactive} icon={UserX} tone="red" supporting="Retained for history"/>{user?.is_admin && <StatCard label="Active teachers" value={data.teachers || 0} icon={GraduationCap} tone="gold" supporting="Teaching profiles"/>}</div>
    <div className="grid-2"><Card><h2>Today’s attendance</h2><div className="attendance-ring" style={attendanceStyle}><strong>{data.attendance_percentage}%</strong><span>Present or late</span></div><div className="legend">{['present', 'absent', 'late', 'excused'].map(status => <span key={status}><i className={status}/>{status} <b>{data.today_attendance[status] || 0}</b></span>)}</div></Card><Card><h2>Recent Hifz updates</h2>{data.recent_hifz.length ? data.recent_hifz.map(item => <div className="activity" key={item.id}><div><strong>{item.student__first_name} {item.student__last_name}</strong><small>Surah {item.surah} · {item.status.replace('_', ' ')}</small></div><b>{item.progress_percentage}%</b></div>) : <Empty text="No recent Hifz updates" description="New progress records will appear here."/>}</Card></div>
  </>;
}
