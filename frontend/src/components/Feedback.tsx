export default function Feedback({message, tone = 'success', onDismiss}: {message: string; tone?: 'success' | 'error'; onDismiss?: () => void}) {
  return <div className={`feedback ${tone}`} role={tone === 'error' ? 'alert' : 'status'}><span>{message}</span>{onDismiss && <button type="button" aria-label="Dismiss message" onClick={onDismiss}>×</button>}</div>;
}
