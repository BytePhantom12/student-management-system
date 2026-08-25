import type {ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes} from 'react';
import type {LucideIcon} from 'lucide-react';
import {Inbox} from 'lucide-react';

export const Button = ({className = '', ...props}: ButtonHTMLAttributes<HTMLButtonElement>) => <button className={`btn ${className}`} {...props}/>;

export const Input = ({label, hint, ...props}: InputHTMLAttributes<HTMLInputElement> & {label?: string; hint?: string}) => <label className="field">{label && <span>{label}</span>}<input {...props}/>{hint && <small>{hint}</small>}</label>;

export const Select = ({label, hint, children, ...props}: SelectHTMLAttributes<HTMLSelectElement> & {label?: string; hint?: string; children: ReactNode}) => <label className="field">{label && <span>{label}</span>}<select {...props}>{children}</select>{hint && <small>{hint}</small>}</label>;

export const Textarea = ({label, hint, ...props}: TextareaHTMLAttributes<HTMLTextAreaElement> & {label?: string; hint?: string}) => <label className="field">{label && <span>{label}</span>}<textarea {...props}/>{hint && <small>{hint}</small>}</label>;

export const Card = ({children, className = ''}: {children: ReactNode; className?: string}) => <section className={`card ${className}`}>{children}</section>;

export const Badge = ({children, tone = 'neutral'}: {children: ReactNode; tone?: string}) => <span className={`badge ${tone}`}>{children}</span>;

export function PageHeader({eyebrow, title, description, actions}: {eyebrow?: string; title: ReactNode; description: string; actions?: ReactNode}) {
  return <div className="page-title"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1><p>{description}</p></div>{actions && <div className="page-actions">{actions}</div>}</div>;
}

export function StatCard({label, value, icon: Icon, supporting, tone = 'emerald', secondary = false}: {label: string; value: ReactNode; icon: LucideIcon; supporting?: ReactNode; tone?: string; secondary?: boolean}) {
  return <Card className={`stat-card ${tone} ${secondary ? 'secondary-stat' : ''}`}><div className="stat-icon"><Icon size={20}/></div><span>{label}</span><strong>{value}</strong>{supporting && <small>{supporting}</small>}</Card>;
}

export function Avatar({name, size = 'md'}: {name: string; size?: 'sm' | 'md' | 'lg'}) {
  const initials = name.trim().split(/\s+/).slice(0, 2).map(part => part[0]?.toUpperCase()).join('') || 'U';
  return <span className={`avatar ${size}`} aria-hidden="true">{initials}</span>;
}

export const Spinner = () => <div className="spinner" role="status" aria-label="Loading"/>;

export function Skeleton({rows = 4, cards = false}: {rows?: number; cards?: boolean}) {
  return <div className={cards ? 'skeleton-grid' : 'skeleton-list'} aria-label="Loading content">{Array.from({length: rows}, (_, index) => <div className="skeleton" key={index}/>)}</div>;
}

export function Empty({text, description, icon: Icon = Inbox, action}: {text: string; description?: string; icon?: LucideIcon; action?: ReactNode}) {
  return <div className="empty"><span className="empty-icon"><Icon size={23}/></span><strong>{text}</strong>{description && <p>{description}</p>}{action}</div>;
}
