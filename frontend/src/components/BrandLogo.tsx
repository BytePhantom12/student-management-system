import {useState} from 'react';
import {BookOpen} from 'lucide-react';

type BrandLogoProps = {
  size?: 'small' | 'medium' | 'large';
  decorative?: boolean;
  className?: string;
};

export default function BrandLogo({size = 'medium', decorative = false, className = ''}: BrandLogoProps) {
  const [failed, setFailed] = useState(false);
  const label = decorative ? undefined : 'Halqatu Darul Taqwa logo';

  return <span className={`brand-logo-frame ${size} ${className}`}>
    {failed
      ? <BookOpen className="brand-logo-fallback" role={decorative ? undefined : 'img'} aria-label={label} aria-hidden={decorative || undefined}/>
      : <img src="/branding/darul-taqwa-logo-transparent.png" alt={decorative ? '' : 'Halqatu Darul Taqwa logo'} onError={() => setFailed(true)}/>}
  </span>;
}
