import axios from 'axios';

function collectMessages(value:unknown,prefix=''):string[]{
  if(typeof value==='string')return [prefix?`${prefix}: ${value}`:value];
  if(Array.isArray(value))return value.flatMap(item=>collectMessages(item,prefix));
  if(value&&typeof value==='object')return Object.entries(value as Record<string,unknown>).flatMap(([key,item])=>collectMessages(item,key==='detail'?prefix:key.replaceAll('_',' ')));
  return [];
}

export function apiErrorMessage(error:unknown,fallback='Unable to complete this request.'){
  if(!axios.isAxiosError(error))return fallback;
  const details=error.response?.data?.error?.details??error.response?.data;
  const messages=collectMessages(details);
  if(messages.length)return messages.join(' ');
  if(error.response?.status===403)return 'You do not have permission to perform this action.';
  return fallback;
}
