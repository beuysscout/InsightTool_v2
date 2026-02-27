-- Insight Tool — Initial Schema
-- Run this in your Supabase SQL Editor to set up all tables.

-- ============================================================
-- PROJECTS
-- ============================================================
create table if not exists projects (
  project_id text primary key,
  name text not null,
  created_at timestamptz not null default now(),
  status text not null default 'setup',
  session_count int not null default 0,
  participant_count int not null default 0
);

-- ============================================================
-- GUIDES
-- One guide per project. Sections/questions stored as JSONB
-- since they are deeply nested and queried as a unit.
-- ============================================================
create table if not exists guides (
  project_id text primary key references projects(project_id) on delete cascade,
  project_name text not null default '',
  objective text not null default '',
  research_goals jsonb not null default '[]',
  sections jsonb not null default '[]',
  version int not null default 1,
  locked boolean not null default false
);

-- ============================================================
-- SESSIONS
-- One row per uploaded transcript. Transcript turns,
-- anonymisation log, and organised data stored as JSONB.
-- ============================================================
create table if not exists sessions (
  session_id text primary key,
  project_id text not null references projects(project_id) on delete cascade,
  participant_id text not null,
  transcript jsonb not null default '[]',
  anonymisation_log jsonb not null default '{"auto_redacted": 0, "researcher_reviewed": 0, "exclusions": 0, "detections": []}',
  organised jsonb,
  upload_timestamp timestamptz not null default now(),
  status text not null default 'uploaded'
);

create index if not exists idx_sessions_project_id on sessions(project_id);

-- ============================================================
-- SESSION_THEMES
-- One row per session. Themes array stored as JSONB.
-- ============================================================
create table if not exists session_themes (
  session_id text primary key references sessions(session_id) on delete cascade,
  participant_id text not null,
  themes jsonb not null default '[]'
);

-- ============================================================
-- ROW LEVEL SECURITY
-- Enable RLS but allow all operations for authenticated users.
-- Tighten these policies based on your auth requirements.
-- ============================================================
alter table projects enable row level security;
alter table guides enable row level security;
alter table sessions enable row level security;
alter table session_themes enable row level security;

-- Policies: allow all for authenticated users
create policy "Allow all for authenticated users" on projects
  for all using (auth.role() = 'authenticated');

create policy "Allow all for authenticated users" on guides
  for all using (auth.role() = 'authenticated');

create policy "Allow all for authenticated users" on sessions
  for all using (auth.role() = 'authenticated');

create policy "Allow all for authenticated users" on session_themes
  for all using (auth.role() = 'authenticated');
