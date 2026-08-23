export type User={id:number;username:string;first_name:string;last_name:string;email:string;role:'admin'|'teacher'};
export type Student={id:number;student_id:string;first_name:string;last_name:string;full_name:string;gender:string;date_of_birth:string;phone:string;email:string;guardian_name:string;guardian_phone:string;guardian_relationship:string;enrollment_date:string;status:'active'|'inactive';assigned_teacher:number|null;teacher_name:string;notes:string};
export type Page<T>={count:number;next:string|null;previous:string|null;results:T[]};

