import axios from 'axios';
import type {AxiosError, InternalAxiosRequestConfig} from 'axios';

type RetriableRequest = InternalAxiosRequestConfig & {_retry?: boolean};
type RefreshResponse = {access: string; refresh?: string};

export const api = axios.create({baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api'});
let refreshPromise: Promise<string> | null = null;

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function refreshAccessToken() {
  if (!refreshPromise) {
    const refresh = localStorage.getItem('refresh');
    refreshPromise = axios.post<RefreshResponse>(`${api.defaults.baseURL}/auth/refresh/`, {refresh})
      .then(({data}) => {
        localStorage.setItem('access', data.access);
        if (data.refresh) localStorage.setItem('refresh', data.refresh);
        return data.access;
      })
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

api.interceptors.response.use(response => response, async (error: AxiosError) => {
  const original = error.config as RetriableRequest | undefined;
  if (error.response?.status === 401 && original && !original._retry && localStorage.getItem('refresh')) {
    original._retry = true;
    try {
      const access = await refreshAccessToken();
      original.headers.Authorization = `Bearer ${access}`;
      return api(original);
    } catch {
      localStorage.clear();
      if (location.pathname !== '/login') location.assign('/login');
    }
  }
  return Promise.reject(error);
});
