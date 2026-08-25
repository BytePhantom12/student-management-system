import {useEffect, useState} from 'react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import {useAuth} from '../context/auth';
import {Badge, Button, Card, Empty, Input, Select, Spinner} from '../components/UI';
import type {AttendanceRecord, AttendanceSession, AttendanceStatus, Page, Student} from '../types';

const statuses: AttendanceStatus[] = ['present', 'absent', 'late', 'excused'];

async function getAllStudents() {
  let url: string | null = '/students/?status=active';
  let rows: Student[] = [];
  while (url) {
    const data: Page<Student> = (await api.get<Page<Student>>(url)).data;
    rows = rows.concat(data.results);
    url = data.next;
  }
  return rows;
}

async function fetchAttendanceData() {
  const [students, sessions, records, statistics] = await Promise.all([
    getAllStudents(),
    api.get<Page<AttendanceSession>>('/attendance/sessions/'),
    api.get<Page<AttendanceRecord>>('/attendance/'),
    api.get<Record<string, number>>('/attendance/statistics/'),
  ]);
  return {students, sessions: sessions.data.results, records: records.data.results, statistics: statistics.data};
}

export default function Attendance() {
  const {user} = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [records, setRecords] = useState<AttendanceRecord[] | null>(null);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [title, setTitle] = useState('');
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [marks, setMarks] = useState<Record<number, AttendanceStatus>>({});
  const [error, setError] = useState('');

  function applyData(data: Awaited<ReturnType<typeof fetchAttendanceData>>) {
    setStudents(data.students);
    setSessions(data.sessions);
    setRecords(data.records);
    setStats(data.statistics);
  }

  useEffect(() => {
    let active = true;
    fetchAttendanceData()
      .then(data => { if (active) applyData(data); })
      .catch(reason => { if (active) { setError(apiErrorMessage(reason, 'Unable to load attendance.')); setRecords([]); } });
    return () => { active = false; };
  }, []);

  async function reload() {
    applyData(await fetchAttendanceData());
  }

  async function createSession() {
    setError('');
    try {
      const {data} = await api.post<AttendanceSession>('/attendance/sessions/', {date, title});
      setSession(data);
      setMarks(Object.fromEntries(students.map(student => [student.id, 'present'])));
      setSessions(current => [data, ...current]);
    } catch (reason) {
      setError(apiErrorMessage(reason, 'Unable to create session.'));
    }
  }

  async function saveRoster() {
    if (!session) return;
    setError('');
    try {
      await api.post('/attendance/bulk/', {records: students.map(student => ({student: student.id, date: session.date, status: marks[student.id] || 'present', session: session.id}))});
      setSession(null);
      await reload();
    } catch (reason) {
      setError(apiErrorMessage(reason, 'Unable to save attendance.'));
    }
  }

  async function changeRecord(record: AttendanceRecord, status: AttendanceStatus) {
    setError('');
    try {
      const {data} = await api.patch<AttendanceRecord>(`/attendance/${record.id}/`, {status});
      setRecords(current => current?.map(item => item.id === record.id ? data : item) || null);
      setStats((await api.get<Record<string, number>>('/attendance/statistics/')).data);
    } catch (reason) {
      setError(apiErrorMessage(reason, 'Unable to edit attendance.'));
    }
  }

  if (!records) return <Spinner/>;
  return <>
    <div className="page-title"><div><h1>Attendance</h1><p>Create sessions and manage attendance for {user?.is_admin ? 'all' : 'your assigned'} students.</p></div></div>
    {error && <div className="alert" role="alert">{error}</div>}
    <div className="stats"><Card><span>Total records</span><strong>{stats.total || 0}</strong></Card><Card><span>Attendance rate</span><strong>{stats.attendance_percentage || 0}%</strong></Card><Card><span>Present</span><strong>{stats.present || 0}</strong></Card><Card><span>Absent</span><strong>{stats.absent || 0}</strong></Card></div>
    <Card><h2>New attendance session</h2><div className="form-grid"><Input label="Date" type="date" value={date} onChange={event => setDate(event.target.value)}/><Input label="Session title" placeholder="e.g. Morning class" value={title} onChange={event => setTitle(event.target.value)}/></div><div className="actions"><Button type="button" onClick={createSession}>Create session</Button></div></Card>
    {session && <Card><h2>Mark attendance — {session.title || session.date}</h2>{students.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>Status</th></tr></thead><tbody>{students.map(student => <tr key={student.id}><td>{student.full_name}</td><td><Select aria-label={`Attendance status for ${student.full_name}`} value={marks[student.id] || 'present'} onChange={event => setMarks(current => ({...current, [student.id]: event.target.value as AttendanceStatus}))}>{statuses.map(status => <option key={status} value={status}>{status}</option>)}</Select></td></tr>)}</tbody></table></div> : <Empty text="No assigned active students."/>}<div className="actions"><Button className="secondary" onClick={() => setSession(null)}>Cancel</Button><Button disabled={!students.length} onClick={saveRoster}>Save attendance</Button></div></Card>}
    <Card><h2>Attendance history</h2>{records.length ? <div className="table-wrap"><table><thead><tr><th>Date</th><th>Student</th><th>Status</th><th>Recorded by</th></tr></thead><tbody>{records.map(record => <tr key={record.id}><td>{record.date}</td><td>{record.student_name}</td><td>{user?.is_admin || record.recorded_by === user?.id ? <Select aria-label={`Attendance status for ${record.student_name} on ${record.date}`} value={record.status} onChange={event => changeRecord(record, event.target.value as AttendanceStatus)}>{statuses.map(status => <option key={status} value={status}>{status}</option>)}</Select> : <Badge tone={record.status}>{record.status}</Badge>}</td><td>{record.recorded_by_name || '—'}</td></tr>)}</tbody></table></div> : <Empty text="No attendance records yet."/>}</Card>
    <Card><h2>Recent sessions</h2>{sessions.length ? sessions.map(item => <div className="activity" key={item.id}><div><strong>{item.title || 'Attendance session'}</strong><small>{item.date} · {item.teacher_name || 'Admin'}</small></div><b>{item.record_count || 0} records</b></div>) : <Empty text="No attendance sessions yet."/>}</Card>
  </>;
}
