create table if not exists contact (
   contact_id int,
   first_name text,
   last_name text
);

create table if not exists address (
   contact_id int,
   address1 text,
   address2 text,
   city text,
   state text,
   zip text
);

create table if not exists phone (
   contact_id int,
   phone text
);

delete from contact;
insert into contact values ( 1, 'George', 'Washington');
insert into contact values ( 2, 'John', 'Adams');
insert into contact values ( 3, 'Thomas', 'Jefferson');

delete from address;
insert into address values ( 1, '123 Main St.', 'Las Vegas', 'Attn: George', 'NV', '89119');
insert into address values ( 2, '456 State Ave.', 'Las Vegas', 'Attn: John', 'NV', '89119');
insert into address values ( 3, '789 Third Rd.', 'Las Vegas', 'Attn: Thomas', 'NV', '89119');

delete from phone;
insert into phone values ( 1, '702-111-1111');
insert into phone values ( 2, '702-222-2222');
insert into phone values ( 3, '702-333-3333');

select a.contact_id 
      ,a.first_name
      ,a.last_name
      ,b.address1 
      ,b.address2 
      ,b.city
      ,b.state
      ,b.zip
      ,c.phone
from contact a
inner join address b
on a.contact_id = b.contact_id
inner join phone c
on a.contact_id = c.contact_id;
