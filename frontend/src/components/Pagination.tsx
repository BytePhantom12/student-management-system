import {Button} from './UI';

export default function Pagination({page, total, pageSize, hasPrevious, hasNext, onPage}: {page: number; total: number; pageSize: number; hasPrevious: boolean; hasNext: boolean; onPage: (page: number) => void}) {
  const start = total ? ((page - 1) * pageSize) + 1 : 0;
  const end = Math.min(page * pageSize, total);
  return <nav className="pagination" aria-label="Pagination"><Button type="button" disabled={!hasPrevious} onClick={() => onPage(page - 1)}>Previous</Button><span aria-live="polite">Showing {start}–{end} of {total} · Page {page}</span><Button type="button" disabled={!hasNext} onClick={() => onPage(page + 1)}>Next</Button></nav>;
}
