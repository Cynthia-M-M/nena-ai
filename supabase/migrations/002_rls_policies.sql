-- NENA AI | MIGRATION 002: TENANT-SCOPED ROW LEVEL SECURITY
create or replace function public.is_platform_admin() returns boolean language sql stable security definer set search_path=public,pg_temp as $$
 select exists(select 1 from public.org_memberships m where m.user_id=auth.uid() and m.active and m.role='platform_admin'); $$;
create or replace function public.is_org_member(target_org uuid) returns boolean language sql stable security definer set search_path=public,pg_temp as $$
 select exists(select 1 from public.org_memberships m where m.organization_id=target_org and m.user_id=auth.uid() and m.active); $$;
create or replace function public.has_org_role(target_org uuid, allowed_roles public.membership_role[]) returns boolean language sql stable security definer set search_path=public,pg_temp as $$
 select exists(select 1 from public.org_memberships m where m.organization_id=target_org and m.user_id=auth.uid() and m.active and m.role=any(allowed_roles)); $$;
create or replace function public.can_access_program(target_program uuid) returns boolean language sql stable security definer set search_path=public,pg_temp as $$
 select exists(select 1 from public.funding_programs p where p.id=target_program and (
  public.is_org_member(p.funder_organization_id) or exists(select 1 from public.clinic_enrollments e where e.program_id=p.id and e.active and public.is_org_member(e.clinic_organization_id)))); $$;

revoke all on function public.is_platform_admin() from public;
revoke all on function public.is_org_member(uuid) from public;
revoke all on function public.has_org_role(uuid,public.membership_role[]) from public;
revoke all on function public.can_access_program(uuid) from public;
grant execute on function public.is_platform_admin() to authenticated;
grant execute on function public.is_org_member(uuid) to authenticated;
grant execute on function public.has_org_role(uuid,public.membership_role[]) to authenticated;
grant execute on function public.can_access_program(uuid) to authenticated;

create policy organizations_member_read on public.organizations for select to authenticated using (public.is_org_member(id) or public.is_platform_admin());
create policy user_profile_self_read on public.user_profiles for select to authenticated using (id=auth.uid() or public.is_platform_admin());
create policy user_profile_self_update on public.user_profiles for update to authenticated using (id=auth.uid()) with check (id=auth.uid());
create policy membership_org_admin_read on public.org_memberships for select to authenticated using (
 user_id=auth.uid() or public.has_org_role(organization_id,array['clinic_admin','funder_admin','platform_admin']::public.membership_role[]));
create policy clinic_profile_member_read on public.clinic_profiles for select to authenticated using (public.is_org_member(organization_id) or public.is_platform_admin());
create policy funding_program_read on public.funding_programs for select to authenticated using (
 public.is_org_member(funder_organization_id) or public.can_access_program(id) or public.is_platform_admin());
create policy program_rules_read on public.program_rules for select to authenticated using (public.can_access_program(program_id) or public.is_platform_admin());
create policy clinic_enrollment_read on public.clinic_enrollments for select to authenticated using (
 public.is_org_member(clinic_organization_id) or public.can_access_program(program_id) or public.is_platform_admin());
create policy patient_token_funder_read on public.patient_tokens for select to authenticated using (
 exists(select 1 from public.funding_programs p where p.id=program_id and (public.is_org_member(p.funder_organization_id) or public.is_platform_admin())));
create policy device_clinic_read on public.registered_devices for select to authenticated using (public.is_org_member(clinic_organization_id) or public.is_platform_admin());
create policy encounter_read on public.care_encounters for select to authenticated using (
 public.is_org_member(clinic_organization_id) or public.can_access_program(program_id) or public.is_platform_admin());
-- No authenticated INSERT/UPDATE/DELETE policies for encounters or consent challenges.
create policy verification_read on public.verification_events for select to authenticated using (
 exists(select 1 from public.care_encounters e where e.id=encounter_id and (
  public.is_org_member(e.clinic_organization_id) or public.can_access_program(e.program_id) or public.is_platform_admin())));
create policy anomaly_funder_read on public.anomaly_assessments for select to authenticated using (
 exists(select 1 from public.care_encounters e join public.funding_programs p on p.id=e.program_id where e.id=encounter_id and (
  public.has_org_role(p.funder_organization_id,array['funder_admin','funder_analyst','auditor','platform_admin']::public.membership_role[]) or public.is_platform_admin())));
create policy ledger_read on public.ledger_entries for select to authenticated using (
 public.is_org_member(clinic_organization_id) or public.is_org_member(funder_organization_id) or public.is_platform_admin());
create policy payout_read on public.payouts for select to authenticated using (
 exists(select 1 from public.ledger_entries l where l.id=ledger_entry_id and (
  public.is_org_member(l.clinic_organization_id) or public.is_org_member(l.funder_organization_id) or public.is_platform_admin())));
-- consent_challenges and ledger_chain_state intentionally have no authenticated policies.
