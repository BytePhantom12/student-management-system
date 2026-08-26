import {useEffect,useState} from 'react';
import {Link,useLocation,useParams} from 'react-router-dom';
import {BookOpen,CalendarCheck,Edit} from 'lucide-react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import type {AttendanceRecord,HifzProgress,Page,Student} from '../types';
import {Badge,Card,Empty,PageHeader,Skeleton} from '../components/UI';
import ProtectedProfileImage from '../components/ProtectedProfileImage';
import StudentNotes from '../components/StudentNotes';
import Feedback from '../components/Feedback';

export default function StudentProfile(){
  const {id}=useParams(); const location=useLocation(); const navigationState=location.state as {message?:string;tone?:'success'|'error'}|null; const [feedback,setFeedback]=useState(navigationState?.message||''); const [feedbackTone]=useState<'success'|'error'>(navigationState?.tone||'success'); const [student,setStudent]=useState<Student|null>(null); const [attendance,setAttendance]=useState<Page<AttendanceRecord>|null>(null); const [hifz,setHifz]=useState<Page<HifzProgress>|null>(null); const [error,setError]=useState('');
  useEffect(()=>{let active=true;Promise.all([api.get<Student>(`/students/${id}/`),api.get<Page<AttendanceRecord>>(`/attendance/?student=${id}&ordering=-date`),api.get<Page<HifzProgress>>(`/hifz/?student=${id}&ordering=-updated_at`)]).then(([studentResponse,attendanceResponse,hifzResponse])=>{if(active){setStudent(studentResponse.data);setAttendance(attendanceResponse.data);setHifz(hifzResponse.data);}}).catch(reason=>{if(active)setError(apiErrorMessage(reason,'Unable to load this student.'));});return()=>{active=false;};},[id]);
  if(!student)return error?<div className="alert" role="alert">{error}</div>:<Skeleton rows={5}/>;
  return <><PageHeader eyebrow="Student records" title="Student Profile" description="Review identity, relationships, attendance, learning progress, and notes." actions={<Link className="btn" to={`/students/${id}/edit`}><Edit size={17}/> Edit student</Link>}/><div className="profile-hero"><ProtectedProfileImage endpoint={`/students/${student.id}/profile-image/`} hasImage={student.has_profile_image} name={student.full_name} size="lg"/><div><h1>{student.full_name}</h1><p>{student.student_id} · {student.gender}</p></div><span className="profile-status"><Badge tone={student.status}>{student.status}</Badge></span></div><div className="profile-grid">
    {feedback&&<div className="wide"><Feedback message={feedback} tone={feedbackTone} onDismiss={()=>setFeedback('')}/></div>}
    <Card><h2>Identity</h2><dl><dt>Student ID</dt><dd>{student.student_id}</dd><dt>Date of birth</dt><dd>{student.date_of_birth}</dd><dt>Gender</dt><dd>{student.gender}</dd><dt>Status</dt><dd><Badge tone={student.status}>{student.status}</Badge></dd></dl></Card>
    <Card><h2>Contact</h2><dl><dt>Phone</dt><dd>{student.phone||'—'}</dd><dt>Email</dt><dd>{student.email||'—'}</dd><dt>Address</dt><dd>{student.address||'—'}</dd></dl></Card>
    <Card><h2>Enrollment</h2><dl><dt>Enrollment date</dt><dd>{student.enrollment_date}</dd><dt>Assigned Teacher</dt><dd>{student.teacher?.name||'Unassigned'}</dd><dt>Teacher phone</dt><dd>{student.teacher?.phone||'—'}</dd><dt>Teacher email</dt><dd>{student.teacher?.email||'—'}</dd></dl></Card>
    <Card><h2>Primary Guardian</h2><dl><dt>Name</dt><dd>{student.parent?.name||'Not assigned'}</dd><dt>Relationship</dt><dd>{student.guardian_relationship||'—'}</dd><dt>Phone</dt><dd>{student.parent?.phone||'—'}</dd><dt>Email</dt><dd>{student.parent?.email||'—'}</dd></dl></Card>
    <Card><h2>Attendance</h2><p className="section-summary"><strong>{attendance?.count||0}</strong> attendance records</p>{attendance?.results.slice(0,3).map(record=><div className="activity" key={record.id}><div><strong>{record.date}</strong><small>{record.recorded_by_name||'Recorded attendance'}</small></div><Badge tone={record.status}>{record.status}</Badge></div>)}<div className="quick-links"><Link to={`/attendance?student=${id}`}><CalendarCheck size={18}/> View full attendance</Link></div></Card>
    <Card><h2>Hifz</h2><p className="section-summary"><strong>{hifz?.count||0}</strong> progress records</p>{hifz?.results.slice(0,3).map(record=><div className="activity" key={record.id}><div><strong>{record.surah_name}</strong><small>Juz {record.juz} · {record.status.replaceAll('_',' ')}</small></div><b>{record.progress_percentage}%</b></div>)}<div className="quick-links"><Link to={`/hifz?student=${id}`}><BookOpen size={18}/> View Hifz progress</Link></div></Card>
    <Card className="wide"><h2>General student notes</h2>{student.notes?<p className="long-copy">{student.notes}</p>:<Empty text="No general notes" description="General record notes can be added from Edit Student."/>}</Card>
    <Card className="wide"><h2>Authored teacher notes</h2><StudentNotes studentId={student.id}/></Card>
    <Card className="wide system-info"><h2>System information</h2><dl><dt>Created</dt><dd>{new Date(student.created_at).toLocaleString()}</dd><dt>Last updated</dt><dd>{new Date(student.updated_at).toLocaleString()}</dd></dl></Card>
  </div></>;
}
