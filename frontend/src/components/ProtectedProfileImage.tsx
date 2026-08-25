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

  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;
    if (!hasImage) return () => { active = false; };
    api.get<Blob>(endpoint, {responseType: 'blob'})
      .then(response => {
        if (!active) return;
        createdUrl = URL.createObjectURL(response.data);
        setLoaded({key: requestKey, url: createdUrl});
      })
      .catch(() => undefined);
    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [endpoint, hasImage, requestKey]);

  const objectUrl = loaded?.key === requestKey ? loaded.url : null;
  if (!objectUrl) return <Avatar name={name} size={size}/>;
  return <span className={`avatar protected-avatar ${size} ${className}`}><img src={objectUrl} alt={`${name} profile`} loading="lazy" decoding="async"/></span>;
}
