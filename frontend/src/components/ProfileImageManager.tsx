import {useState} from 'react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import ProfileImageEditor from './ProfileImageEditor';
import {Button} from './UI';
import Feedback from './Feedback';

export default function ProfileImageManager({name, endpoint, hasImage, onChanged}: {name: string; endpoint: string; hasImage: boolean; onChanged?: (hasImage: boolean) => void}) {
  const [current, setCurrent] = useState(hasImage);
  const [file, setFile] = useState<File | null>(null);
  const [removeRequested, setRemoveRequested] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');
  async function save() {
    setBusy(true); setError(''); setFeedback('');
    try {
      if (file) {
        const payload = new FormData(); payload.append('image', file);
        await api.post(endpoint, payload);
        setCurrent(true); setFile(null); setRemoveRequested(false); onChanged?.(true); setFeedback('Profile photo updated.');
      } else if (removeRequested && current) {
        await api.delete(endpoint);
        setCurrent(false); setRemoveRequested(false); onChanged?.(false); setFeedback('Profile photo removed.');
      }
    } catch (reason) {
      setError(apiErrorMessage(reason, 'Unable to update the profile photo.'));
    } finally { setBusy(false); }
  }

  return <div className="profile-image-manager">
    {error && <Feedback tone="error" message={error} onDismiss={() => setError('')}/>}
    {feedback && <Feedback message={feedback} onDismiss={() => setFeedback('')}/>}
    <ProfileImageEditor name={name} endpoint={endpoint} hasImage={current} file={file} removeRequested={removeRequested} disabled={busy} onFile={selected => {setFile(selected); setRemoveRequested(false);}} onRemove={() => {setFile(null); setRemoveRequested(true);}} onError={setError}/>
    <div className="actions"><Button type="button" disabled={busy || (!file && !removeRequested)} onClick={save}>{busy ? 'Saving…' : 'Save photo'}</Button></div>
  </div>;
}
