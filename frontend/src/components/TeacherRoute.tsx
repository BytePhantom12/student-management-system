import {Navigate,Outlet,useLocation} from 'react-router-dom';
import {useAuth} from '../context/auth';
import {Spinner} from './UI';

export default function TeacherRoute(){
  const {user,loading}=useAuth();
  const location=useLocation();
  if(loading)return <Spinner/>;
  if(!user)return <Navigate to="/login" state={{from:location.pathname}} replace/>;
  return user.role==='teacher'?<Outlet/>:<Navigate to="/dashboard" replace/>;
}
