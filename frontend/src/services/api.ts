import axios from 'axios';
export const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api'});
api.interceptors.request.use(c=>{const token=localStorage.getItem('access');if(token)c.headers.Authorization=`Bearer ${token}`;return c});
api.interceptors.response.use(r=>r,async error=>{const original=error.config;if(error.response?.status===401&&!original._retry&&localStorage.getItem('refresh')){original._retry=true;try{const {data}=await axios.post(`${api.defaults.baseURL}/auth/refresh/`,{refresh:localStorage.getItem('refresh')});localStorage.setItem('access',data.access);return api(original)}catch{localStorage.clear();location.href='/login'}}return Promise.reject(error)});

