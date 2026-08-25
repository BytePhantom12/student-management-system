import {api} from '../services/api';
import type {Page} from '../types';

export async function getAllPages<T>(initialUrl:string):Promise<T[]> {
  let url:string|null=initialUrl;
  const rows:T[]=[];
  while(url){
    const response=await api.get<Page<T>>(url);
    const data:Page<T>=response.data;
    rows.push(...data.results);
    url=data.next;
  }
  return rows;
}
