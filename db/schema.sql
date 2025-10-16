create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";
create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  file_name text not null,
  file_url text not null,
  category text,
  doc_type text,
  supplier text,
  issue_date date,
  amount numeric(10,2),
  text_content text,
  ai_confidence numeric(5,2),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  deleted_at timestamptz
);
create table if not exists categories (
  id bigserial primary key,
  name text unique not null,
  created_by uuid,
  created_at timestamptz default now()
);
alter table documents enable row level security;
alter table categories enable row level security;
drop policy if exists "docs_select_own" on documents;
create policy "docs_select_own" on documents for select using (auth.uid() = user_id);
drop policy if exists "docs_insert_own" on documents;
create policy "docs_insert_own" on documents for insert with check (auth.uid() = user_id);
drop policy if exists "docs_update_own" on documents;
create policy "docs_update_own" on documents for update using (auth.uid() = user_id);
drop policy if exists "docs_delete_own" on documents;
create policy "docs_delete_own" on documents for delete using (auth.uid() = user_id);
