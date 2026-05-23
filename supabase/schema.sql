create extension if not exists "pgcrypto";

create table founders (
  id          uuid primary key default gen_random_uuid(),
  email       text unique not null,
  plan        text not null default 'launch',
  credit_balance integer not null default 0,
  created_at  timestamptz not null default now()
);

create table goals (
  id              text primary key,
  founder_id      uuid not null references founders(id),
  instruction     text not null,
  status          text not null default 'pending',
  constraints     jsonb default '{}',
  elapsed_seconds float,
  created_at      timestamptz not null default now(),
  completed_at    timestamptz
);

create table tasks (
  id               text primary key,
  goal_id          text not null references goals(id),
  founder_id       uuid not null references founders(id),
  agent            text not null,
  instruction      text not null,
  context_bundle   jsonb default '{}',
  depends_on       text[] not null default '{}',
  tools_available  text[] not null default '{}',
  constraints      jsonb default '{}',
  status           text not null default 'pending',
  result           jsonb,
  approval_required boolean not null default false,
  created_at       timestamptz not null default now(),
  completed_at     timestamptz
);

create table approvals (
  id              uuid primary key default gen_random_uuid(),
  task_id         text not null references tasks(id),
  founder_id      uuid not null references founders(id),
  agent           text not null,
  action          text not null,
  consequence     text not null,
  documents_ready text[] default '{}',
  approval_token  text unique not null,
  expires_at      timestamptz not null,
  approved_at     timestamptz,
  rejected_at     timestamptz,
  reject_reason   text,
  created_at      timestamptz not null default now()
);

create table memory_documents (
  id          uuid primary key default gen_random_uuid(),
  founder_id  uuid not null references founders(id),
  namespace   text not null,
  agent       text not null,
  task_id     text references tasks(id),
  doc_type    text not null,
  content     text not null,
  summary     text not null,
  metadata    jsonb default '{}',
  created_at  timestamptz not null default now()
);

create index on tasks(goal_id, status);
create index on memory_documents(founder_id, namespace);
