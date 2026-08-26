export function enumLabel(value:string){return value.replaceAll('_',' ').replace(/\b\w/g,character=>character.toUpperCase());}
