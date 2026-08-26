import {useEffect, useState} from 'react';
import {api} from '../services/api';
import {Avatar} from './UI';

type Props = {
  endpoint: string;
  hasImage: boolean;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  version?: number;
  className?: string;
};

export default function ProtectedProfileImage({endpoint, hasImage, name, size = 'md', version = 0, className = ''}: Props) {
  const requestKey = `${endpoint}:${version}`;
  const [loaded, setLoaded] = useState<{key: string; url: string} | null>(null);
  const [attempt,setAttempt]=useState(0);const [failed,setFailed]=useState(false);const [loading,setLoading]=useState(hasImage);

  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;
    if (!hasImage) return () => { active = false; };
    api.get<Blob>(endpoint, {responseType: 'blob'})
      .then(response => {
        if (!active) return;
        createdUrl = URL.createObjectURL(response.data);
        setLoaded({key: requestKey, url: createdUrl});setLoading(false);
      })
      .catch(() => {if(active){setFailed(true);setLoading(false);}});
    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [endpoint, hasImage, requestKey,attempt]);

  const objectUrl = loaded?.key === requestKey ? loaded.url : null;
  if (!objectUrl) return <span className={`protected-avatar-state ${className}`} aria-busy={loading}>{<Avatar name={name} size={size}/>} {failed&&<button type="button" className="avatar-retry" aria-label={`Retry ${name} profile image`} onClick={()=>{setFailed(false);setLoading(true);setAttempt(value=>value+1);}}>Retry</button>}</span>;
  return <span className={`avatar protected-avatar ${size} ${className}`}><img src={objectUrl} alt={`${name} profile`} loading="lazy" decoding="async"/></span>;
}
