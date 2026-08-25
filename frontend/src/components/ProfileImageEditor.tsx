import {useEffect, useId, useState} from 'react';
import {ImagePlus, Trash2} from 'lucide-react';
import ProtectedProfileImage from './ProtectedProfileImage';
import {Button} from './UI';

type Props = {
  name: string;
  endpoint?: string;
  hasImage: boolean;
  file: File | null;
  removeRequested: boolean;
  disabled?: boolean;
  onFile: (file: File | null) => void;
  onRemove: () => void;
  onError: (message: string) => void;
};

const MAX_BYTES = 3 * 1024 * 1024;
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function LocalPreview({file, name}: {file: File; name: string}) {
  const [url] = useState(() => URL.createObjectURL(file));
  useEffect(() => () => URL.revokeObjectURL(url), [url]);
  return <span className="avatar protected-avatar lg"><img src={url} alt={`${name} selected profile preview`} decoding="async"/></span>;
}

export default function ProfileImageEditor({name, endpoint, hasImage, file, removeRequested, disabled, onFile, onRemove, onError}: Props) {
  const inputId = useId();

  function select(selected?: File) {
    if (!selected) return;
    if (!ALLOWED_TYPES.has(selected.type)) { onError('Use a JPEG, PNG, or WebP profile photo.'); return; }
    if (selected.size > MAX_BYTES) { onError('Profile photos must be 3 MB or smaller.'); return; }
    onError('');
    onFile(selected);
  }

  const showCurrent = Boolean(endpoint && hasImage && !removeRequested && !file);
  return <div className="profile-image-editor">
    <div className="profile-image-preview">
      {file ? <LocalPreview key={`${file.name}:${file.lastModified}:${file.size}`} file={file} name={name}/> : showCurrent ? <ProtectedProfileImage endpoint={endpoint!} hasImage name={name} size="lg"/> : <ProtectedProfileImage endpoint="" hasImage={false} name={name} size="lg"/>}
    </div>
    <div className="profile-image-controls">
      <strong>Profile Photo</strong>
      <small>JPEG, PNG, or WebP. Maximum 3 MB. Images are resized and stored privately.</small>
      <div>
        <label className={`btn secondary ${disabled ? 'disabled' : ''}`} htmlFor={inputId}><ImagePlus size={16}/> {hasImage || file ? 'Replace photo' : 'Choose photo'}</label>
        <input id={inputId} className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" disabled={disabled} onChange={event => select(event.target.files?.[0])}/>
        {(hasImage || file) && !removeRequested && <Button type="button" className="ghost compact" disabled={disabled} onClick={onRemove}><Trash2 size={15}/> Remove</Button>}
      </div>
      {removeRequested && <small className="removal-note">The current photo will be removed when you save.</small>}
    </div>
  </div>;
}
