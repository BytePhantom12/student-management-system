const dateFormatter=new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric'});
const dateTimeFormatter=new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
export function formatDate(value:string|null|undefined){if(!value)return '—';const parsed=/^\d{4}-\d{2}-\d{2}$/.test(value)?new Date(`${value}T00:00:00`):new Date(value);return Number.isNaN(parsed.getTime())?'—':dateFormatter.format(parsed);}
export function formatDateTime(value:string|null|undefined){if(!value)return '—';const parsed=new Date(value);return Number.isNaN(parsed.getTime())?'—':dateTimeFormatter.format(parsed);}
