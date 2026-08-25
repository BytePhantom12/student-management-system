import {useEffect, useState} from 'react';
import {api} from '../services/api';
import {apiErrorMessage} from '../utils/apiError';
import {Card, Empty, Spinner} from '../components/UI';

export default function ResourcePage({title, endpoint}: {title: string; endpoint: string}) {
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api.get(endpoint)
      .then(response => { if (active) setRows(response.data.results || response.data); })
      .catch(reason => { if (active) { setError(apiErrorMessage(reason, `Unable to load ${title.toLowerCase()}.`)); setRows([]); } });
    return () => { active = false; };
  }, [endpoint, title]);
  return <><div className="page-title"><div><h1>{title}</h1><p>Review and manage {title.toLowerCase()} records.</p></div></div><Card>{error && <div className="alert" role="alert">{error}</div>}{!rows ? <Spinner/> : !rows.length ? <Empty text={`No ${title.toLowerCase()} records available.`}/> : <div className="table-wrap"><table><thead><tr>{Object.keys(rows[0]).filter(key => !['created_at', 'updated_at'].includes(key)).slice(0, 6).map(key => <th key={key}>{key.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id || index)}>{Object.entries(row).filter(([key]) => !['created_at', 'updated_at'].includes(key)).slice(0, 6).map(([key, value]) => <td key={key}>{typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—')}</td>)}</tr>)}</tbody></table></div>}</Card></>;
}
