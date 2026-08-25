import {Button} from './UI';

export default function Pagination({page,total,hasPrevious,hasNext,onPage}:{page:number;total:number;pageSize?:number;hasPrevious:boolean;hasNext:boolean;onPage:(page:number)=>void}){
  return <nav className="pagination" aria-label="Pagination"><Button type="button" disabled={!hasPrevious} onClick={()=>onPage(page-1)}>Previous</Button><span aria-live="polite">{total} records · Page {page}</span><Button type="button" disabled={!hasNext} onClick={()=>onPage(page+1)}>Next</Button></nav>;
}
