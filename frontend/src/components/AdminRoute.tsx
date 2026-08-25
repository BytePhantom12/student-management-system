import {Navigate,Outlet} from 'react-router-dom';
import {useAuth} from '../context/auth';
import {Spinner} from './UI';

export default function AdminRoute(){const {user,loading}=useAuth();if(loading)return <Spinner/>;return user?.is_admin?<Outlet/>:<Navigate to="/dashboard" replace/>;}
