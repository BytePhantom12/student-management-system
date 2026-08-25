import {useEffect, useState} from 'react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import type {TeacherSelf} from '../types';
import {Badge, Card, PageHeader, Skeleton} from '../components/UI';
import Feedback from '../components/Feedback';
import ProtectedProfileImage from '../components/ProtectedProfileImage';
import ProfileImageManager from '../components/ProfileImageManager';

export default function TeacherProfile() {
  const [teacher, setTeacher] = useState<TeacherSelf | null>(null);
  const [error, setError] = useState('');
  const [imageVersion, setImageVersion] = useState(0);
  useEffect(() => {let active = true; api.get<TeacherSelf>('/teachers/me/').then(response => {if (active) setTeacher(response.data);}).catch(reason => {if (active) setError(apiErrorMessage(reason, 'Unable to load your teacher profile.'));}); return () => {active = false;};}, []);
  if (!teacher) return error ? <Feedback tone="error" message={error}/> : <Skeleton rows={5}/>;
  return <>
    <PageHeader eyebrow="My account" title="Teacher Profile" description="Review your teacher identity and manage your private profile photo."/>
    <div className="profile-hero"><ProtectedProfileImage endpoint="/teachers/me/profile-image/" hasImage={teacher.has_profile_image} name={teacher.full_name} size="lg" version={imageVersion}/><div><h1>{teacher.full_name}</h1><p>@{teacher.username} · {teacher.role}</p></div><span className="profile-status"><Badge tone={teacher.is_active ? 'active' : 'inactive'}>{teacher.is_active ? 'Active' : 'Inactive'}</Badge></span></div>
    <div className="profile-grid"><Card><h2>Profile information</h2><dl><dt>Username</dt><dd>@{teacher.username}</dd><dt>Email</dt><dd>{teacher.email || '—'}</dd><dt>Phone</dt><dd>{teacher.phone || '—'}</dd><dt>Role</dt><dd><Badge tone="teacher">Teacher</Badge></dd></dl></Card><Card><h2>Profile photo</h2><ProfileImageManager name={teacher.full_name} endpoint="/teachers/me/profile-image/" hasImage={teacher.has_profile_image} onChanged={hasImage => {setTeacher(current => current ? {...current, has_profile_image: hasImage} : current); setImageVersion(value => value + 1);}}/></Card></div>
  </>;
}
