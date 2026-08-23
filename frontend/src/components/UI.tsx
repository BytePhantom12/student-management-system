import type {ButtonHTMLAttributes,InputHTMLAttributes,ReactNode,SelectHTMLAttributes} from 'react';
export const Button=({className='',...p}:ButtonHTMLAttributes<HTMLButtonElement>)=><button className={`btn ${className}`} {...p}/>;
export const Input=({label,...p}:InputHTMLAttributes<HTMLInputElement>&{label?:string})=><label className="field">{label&&<span>{label}</span>}<input {...p}/></label>;
export const Select=({label,children,...p}:SelectHTMLAttributes<HTMLSelectElement>&{label?:string;children:ReactNode})=><label className="field">{label&&<span>{label}</span>}<select {...p}>{children}</select></label>;
export const Card=({children,className=''}:{children:ReactNode;className?:string})=><section className={`card ${className}`}>{children}</section>;
export const Badge=({children,tone='neutral'}:{children:ReactNode;tone?:string})=><span className={`badge ${tone}`}>{children}</span>;
export const Spinner=()=> <div className="spinner" aria-label="Loading"/>;
export const Empty=({text}:{text:string})=><div className="empty">{text}</div>;

