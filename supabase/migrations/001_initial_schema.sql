-- NENA AI | MIGRATION 001: CORE SCHEMA + APPEND-ONLY LEDGER
create extension if not exists pgcrypto with schema extensions;

do $$ begin create type public.organization_type as enum ('clinic','ngo','government','platform'); exception when duplicate_object then null; end $$;
do $$ begin create type public.organization_status as enum ('pending','active','suspended'); exception when duplicate_object then null; end $$;
do $$ begin create type public.membership_role as enum ('platform_admin','clinic_admin','clinic_staff','funder_admin','funder_analyst','auditor'); exception when duplicate_object then null; end $$;
do $$ begin create type public.encounter_status as enum ('draft','submitted','pending_verification','approved','manual_audit','rejected','settlement_pending','settled'); exception when duplicate_object then null; end $$;
do $$ begin create type public.verification_stage as enum ('identity_device','patient_consent','program_policy','anomaly_detection'); exception when duplicate_object then null; end $$;
do $$ begin create type public.verification_status as enum ('passed','failed','flagged'); exception when duplicate_object then null; end $$;
do $$ begin create type public.ledger_event_type as enum ('subsidy_authorized','settlement_confirmed','settlement_failed','reversal','adjustment'); exception when duplicate_object then null; end $$;
do $$ begin create type public.payout_status as enum ('initiated','processing','completed','failed','reversed'); exception when duplicate_object then null; end $$;

create table if not exists public.organizations (
 id uuid primary key default gen_random_uuid(), name text not null,
 organization_type public.organization_type not null,
 registration_number text unique,
 status public.organization_status not null default 'pending',
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.user_profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 full_name text not null, phone_encrypted text,
 account_active boolean not null default true, created_at timestamptz not null default now()
);
create table if not exists public.org_memberships (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.organizations(id),
 user_id uuid not null references public.user_profiles(id),
 role public.membership_role not null, active boolean not null default true,
 created_at timestamptz not null default now(), unique (organization_id,user_id)
);
create index if not exists idx_memberships_user on public.org_memberships(user_id);
create index if not exists idx_memberships_org on public.org_memberships(organization_id);

create table if not exists public.clinic_profiles (
 organization_id uuid primary key references public.organizations(id),
 facility_code text not null unique, county text not null, sub_county text,
 physical_address text, phone_encrypted text,
 latitude numeric(10,7), longitude numeric(10,7),
 verification_status text not null default 'pending'
   check (verification_status in ('pending','verified','rejected')),
 created_at timestamptz not null default now(),
 check (latitude is null or latitude between -90 and 90),
 check (longitude is null or longitude between -180 and 180)
);
create table if not exists public.funding_programs (
 id uuid primary key default gen_random_uuid(),
 funder_organization_id uuid not null references public.organizations(id),
 program_name text not null, description text,
 currency char(3) not null default 'KES' check (currency in ('KES','USD')),
 allocated_amount numeric(18,2) not null check (allocated_amount > 0),
 starts_at timestamptz not null, ends_at timestamptz, active boolean not null default true,
 created_at timestamptz not null default now(),
 check (ends_at is null or ends_at > starts_at), unique (id,funder_organization_id)
);
create index if not exists idx_programs_funder on public.funding_programs(funder_organization_id);
create table if not exists public.program_rules (
 id uuid primary key default gen_random_uuid(), program_id uuid not null references public.funding_programs(id),
 max_amount_per_visit numeric(18,2) not null check (max_amount_per_visit > 0),
 approved_treatment_codes text[] not null, allowed_counties text[] not null,
 requires_patient_otp boolean not null default true,
 max_daily_claims integer not null default 100 check (max_daily_claims > 0),
 max_household_claims_per_day integer not null default 3 check (max_household_claims_per_day > 0),
 geo_fence_radius_m integer check (geo_fence_radius_m is null or geo_fence_radius_m > 0),
 active boolean not null default true, version integer not null default 1 check (version > 0),
 created_at timestamptz not null default now(), unique (program_id,version)
);
create table if not exists public.clinic_enrollments (
 id uuid primary key default gen_random_uuid(),
 clinic_organization_id uuid not null references public.organizations(id),
 program_id uuid not null references public.funding_programs(id),
 active boolean not null default true, approved_at timestamptz,
 created_at timestamptz not null default now(),
 unique (clinic_organization_id,program_id)
);
create table if not exists public.patient_tokens (
 id uuid primary key default gen_random_uuid(), program_id uuid not null references public.funding_programs(id),
 patient_ref_hash text not null, phone_encrypted text,
 coverage_status text not null default 'active' check (coverage_status in ('active','suspended','expired')),
 valid_from timestamptz not null default now(), valid_until timestamptz,
 created_at timestamptz not null default now(),
 unique (program_id,patient_ref_hash), unique (id,program_id),
 check (valid_until is null or valid_until > valid_from)
);
create index if not exists idx_patient_coverage on public.patient_tokens(program_id,coverage_status);
create table if not exists public.registered_devices (
 id uuid primary key default gen_random_uuid(), clinic_organization_id uuid not null references public.organizations(id),
 device_fingerprint_hash text not null, device_name text, active boolean not null default true,
 last_seen_at timestamptz, registered_at timestamptz not null default now(),
 unique (clinic_organization_id,device_fingerprint_hash), unique (id,clinic_organization_id)
);
create table if not exists public.care_encounters (
 id uuid primary key default gen_random_uuid(), clinic_organization_id uuid not null, program_id uuid not null,
 patient_token_id uuid not null, submitted_by uuid not null references public.user_profiles(id), device_id uuid not null,
 treatment_code text not null, description text, amount numeric(18,2) not null check (amount > 0),
 currency char(3) not null default 'KES' check (currency in ('KES','USD')),
 county text not null, occurred_at timestamptz not null, submitted_at timestamptz not null default now(),
 status public.encounter_status not null default 'draft', idempotency_key uuid not null,
 offline_created boolean not null default false, synced_at timestamptz, created_at timestamptz not null default now(),
 foreign key (clinic_organization_id,program_id) references public.clinic_enrollments(clinic_organization_id,program_id),
 foreign key (patient_token_id,program_id) references public.patient_tokens(id,program_id),
 foreign key (device_id,clinic_organization_id) references public.registered_devices(id,clinic_organization_id),
 unique (clinic_organization_id,idempotency_key), unique (id,program_id),
 check (occurred_at <= submitted_at + interval '5 minutes')
);
create index if not exists idx_encounter_clinic on public.care_encounters(clinic_organization_id);
create index if not exists idx_encounter_program on public.care_encounters(program_id);
create index if not exists idx_encounter_status on public.care_encounters(status);
create index if not exists idx_encounter_patient on public.care_encounters(patient_token_id);
create index if not exists idx_encounter_date on public.care_encounters(occurred_at desc);
create table if not exists public.consent_challenges (
 id uuid primary key default gen_random_uuid(), encounter_id uuid not null references public.care_encounters(id),
 otp_hash text not null, expires_at timestamptz not null, verified_at timestamptz,
 attempts integer not null default 0 check (attempts >= 0), created_at timestamptz not null default now()
);
create index if not exists idx_consent_encounter on public.consent_challenges(encounter_id);
create table if not exists public.verification_events (
 id uuid primary key default gen_random_uuid(), encounter_id uuid not null references public.care_encounters(id),
 stage public.verification_stage not null, status public.verification_status not null,
 reason_code text, details jsonb not null default '{}'::jsonb,
 verified_by text not null default 'system', created_at timestamptz not null default now()
);
create index if not exists idx_verification_encounter on public.verification_events(encounter_id,created_at);
create table if not exists public.anomaly_assessments (
 id uuid primary key default gen_random_uuid(), encounter_id uuid not null references public.care_encounters(id),
 risk_score numeric(5,2) not null check (risk_score between 0 and 100),
 risk_level text not null check (risk_level in ('low','medium','high','critical')),
 flags jsonb not null default '[]'::jsonb,
 recommended_action text not null check (recommended_action in ('approve','manual_audit','reject')),
 created_at timestamptz not null default now()
);
create index if not exists idx_anomaly_encounter on public.anomaly_assessments(encounter_id,created_at desc);

-- Single chain-head row serializes hash generation. Insert is idempotent.
create table if not exists public.ledger_chain_state (
 id smallint primary key check (id = 1), last_hash text not null check (length(last_hash) = 64),
 updated_at timestamptz not null default now()
);
insert into public.ledger_chain_state(id,last_hash) values (1,repeat('0',64)) on conflict (id) do nothing;

-- Append-only event stream: multiple events per encounter are supported.
create table if not exists public.ledger_entries (
 id uuid primary key default gen_random_uuid(), encounter_id uuid not null, program_id uuid not null,
 clinic_organization_id uuid not null references public.organizations(id), funder_organization_id uuid not null,
 event_type public.ledger_event_type not null, amount numeric(18,2) not null check (amount > 0),
 currency char(3) not null check (currency in ('KES','USD')),
 prev_hash text not null, tx_hash text not null unique, metadata jsonb not null default '{}'::jsonb,
 created_by uuid, created_at timestamptz not null default now(),
 foreign key (encounter_id,program_id) references public.care_encounters(id,program_id),
 foreign key (program_id,funder_organization_id) references public.funding_programs(id,funder_organization_id)
);
create index if not exists idx_ledger_program on public.ledger_entries(program_id,created_at desc);
create index if not exists idx_ledger_clinic on public.ledger_entries(clinic_organization_id,created_at desc);
create index if not exists idx_ledger_funder on public.ledger_entries(funder_organization_id,created_at desc);
create table if not exists public.payouts (
 id uuid primary key default gen_random_uuid(), ledger_entry_id uuid not null unique references public.ledger_entries(id),
 provider text not null default 'MPESA_MOCK', provider_transaction_id text unique, phone_encrypted text,
 amount numeric(18,2) not null check (amount > 0), currency char(3) not null default 'KES' check (currency in ('KES','USD')),
 status public.payout_status not null default 'initiated', provider_response jsonb not null default '{}'::jsonb,
 initiated_at timestamptz not null default now(), completed_at timestamptz, updated_at timestamptz not null default now(),
 check ((status = 'completed' and completed_at is not null) or status <> 'completed')
);
create index if not exists idx_payout_status on public.payouts(status,initiated_at desc);

create or replace function public.set_updated_at() returns trigger language plpgsql set search_path = public,pg_temp as $$
begin new.updated_at := now(); return new; end; $$;
drop trigger if exists trg_organizations_updated on public.organizations;
create trigger trg_organizations_updated before update on public.organizations for each row execute function public.set_updated_at();
drop trigger if exists trg_payouts_updated on public.payouts;
create trigger trg_payouts_updated before update on public.payouts for each row execute function public.set_updated_at();

create or replace function public.generate_ledger_hash() returns trigger language plpgsql security definer set search_path = public,extensions,pg_temp as $$
declare previous_hash text; canonical_payload text;
begin
 select last_hash into previous_hash from public.ledger_chain_state where id=1 for update;
 if previous_hash is null then raise exception 'Ledger chain state is missing'; end if;
 new.prev_hash := previous_hash;
 canonical_payload := jsonb_build_object(
  'id',new.id,'encounter_id',new.encounter_id,'program_id',new.program_id,
  'clinic_organization_id',new.clinic_organization_id,'funder_organization_id',new.funder_organization_id,
  'event_type',new.event_type,'amount',new.amount,'currency',new.currency,
  'prev_hash',new.prev_hash,'metadata',new.metadata,'created_by',new.created_by,'created_at',new.created_at
 )::text;
 new.tx_hash := encode(extensions.digest(convert_to(canonical_payload,'UTF8'),'sha256'),'hex');
 update public.ledger_chain_state set last_hash=new.tx_hash,updated_at=now() where id=1;
 return new;
end; $$;
drop trigger if exists trg_ledger_hash on public.ledger_entries;
create trigger trg_ledger_hash before insert on public.ledger_entries for each row execute function public.generate_ledger_hash();
create or replace function public.prevent_ledger_mutation() returns trigger language plpgsql set search_path=public,pg_temp as $$
begin raise exception 'Ledger entries are immutable; append a compensating event instead.'; end; $$;
drop trigger if exists trg_ledger_no_update_delete on public.ledger_entries;
create trigger trg_ledger_no_update_delete before update or delete on public.ledger_entries for each row execute function public.prevent_ledger_mutation();
create or replace function public.prevent_ledger_truncate() returns trigger language plpgsql set search_path=public,pg_temp as $$
begin raise exception 'Ledger entries cannot be truncated.'; end; $$;
drop trigger if exists trg_ledger_no_truncate on public.ledger_entries;
create trigger trg_ledger_no_truncate before truncate on public.ledger_entries for each statement execute function public.prevent_ledger_truncate();

revoke all on public.ledger_chain_state from anon,authenticated;
revoke insert,update,delete,truncate on public.ledger_entries from anon,authenticated;
grant select on public.ledger_entries to authenticated;

alter table public.organizations enable row level security;
alter table public.user_profiles enable row level security;
alter table public.org_memberships enable row level security;
alter table public.clinic_profiles enable row level security;
alter table public.funding_programs enable row level security;
alter table public.program_rules enable row level security;
alter table public.clinic_enrollments enable row level security;
alter table public.patient_tokens enable row level security;
alter table public.registered_devices enable row level security;
alter table public.care_encounters enable row level security;
alter table public.consent_challenges enable row level security;
alter table public.verification_events enable row level security;
alter table public.anomaly_assessments enable row level security;
alter table public.ledger_chain_state enable row level security;
alter table public.ledger_entries enable row level security;
alter table public.payouts enable row level security;
revoke all on all tables in schema public from anon;
