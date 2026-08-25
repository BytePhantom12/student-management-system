import {useEffect, useState} from 'react';
import {GraduationCap, UserCheck, UserX, Users} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import {api} from '../services/api';
import {useAuth} from '../context/auth';
import {Card, Spinner} from '../components/UI';

type Data = {
  students: {total: number; active: number; inactive: number};
  teachers?: number;
  attendance_percentage: number;
  today_attendance: Record<string, number>;
  recent_hifz: {id: number; student__first_name: string; student__last_name: string; surah: number; progress_percentage: number; status: string}[];
};

export default function Dashboard() {
  const {user} = useAuth();
  const [data, setData] = useState<Data | null>(null);

  useEffect(() => {
    api.get(`/dashboard/${user?.is_admin ? 'admin' : 'teacher'}/`).then(response => setData(response.data));
  }, [user]);

  if (!data) return <Spinner/>;
  const cards: [string, number, LucideIcon][] = [
    ['Students', data.students.total, Users],
    ['Active', data.students.active, UserCheck],
    ['Inactive', data.students.inactive, UserX],
    ...(user?.is_admin ? [['Teachers', data.teachers || 0, GraduationCap] as [string, number, LucideIcon]] : []),
  ];

  return <>
    <div className="page-title"><div><h1>Assalamu alaikum, {user?.first_name}</h1><p>Here is today’s institution overview.</p></div></div>
    <div className="stats">{cards.map(([label, value, Icon]) => <Card key={label}><Icon/><span>{label}</span><strong>{value}</strong></Card>)}</div>
    <div className="grid-2">
      <Card><h2>Today’s attendance</h2><div className="attendance-ring"><strong>{data.attendance_percentage}%</strong><span>Present or late</span></div><div className="legend">{['present', 'absent', 'late', 'excused'].map(status => <span key={status}><i className={status}/>{status} <b>{data.today_attendance[status] || 0}</b></span>)}</div></Card>
      <Card><h2>Recent Hifz updates</h2>{data.recent_hifz.length ? data.recent_hifz.map(item => <div className="activity" key={item.id}><div><strong>{item.student__first_name} {item.student__last_name}</strong><small>Surah {item.surah} · {item.status.replace('_', ' ')}</small></div><b>{item.progress_percentage}%</b></div>) : <p className="muted">No recent updates.</p>}</Card>
    </div>
  </>;
}
