-- NENA AI | SYNTHETIC KENYAN DEMO DATA — development/demo only
-- No real people, national IDs, phone numbers or credentials.
insert into public.organizations(id,name,organization_type,registration_number,status) values
 ('10000000-0000-4000-8000-000000000001','AfyaBridge Foundation','ngo','DEMO-NGO-001','active'),
 ('20000000-0000-4000-8000-000000000001','Mwangaza Community Clinic','clinic','DEMO-CLINIC-001','active'),
 ('20000000-0000-4000-8000-000000000002','Lakeview Family Health Centre','clinic','DEMO-CLINIC-002','active')
on conflict(id) do nothing;
insert into public.clinic_profiles(organization_id,facility_code,county,sub_county,physical_address,latitude,longitude,verification_status) values
 ('20000000-0000-4000-8000-000000000001','KE-DEMO-NAI-001','Nairobi','Westlands','Demo Road, Nairobi',-1.2676,36.8108,'verified'),
 ('20000000-0000-4000-8000-000000000002','KE-DEMO-KSM-001','Kisumu','Kisumu Central','Demo Avenue, Kisumu',-0.0917,34.7680,'verified')
on conflict(organization_id) do nothing;
insert into public.funding_programs(id,funder_organization_id,program_name,description,currency,allocated_amount,starts_at,ends_at,active) values
 ('40000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','Community Essential Care Subsidy',
  'Synthetic demo program for eligible maternal, paediatric and malaria services.','KES',5000000.00,now()-interval '1 day',now()+interval '1 year',true)
on conflict(id) do nothing;
insert into public.program_rules(program_id,max_amount_per_visit,approved_treatment_codes,allowed_counties,requires_patient_otp,max_daily_claims,max_household_claims_per_day,active,version) values
 ('40000000-0000-4000-8000-000000000001',5000.00,
  array['MATERNAL_CARE','PEDIATRIC_EMERGENCY','MALARIA_LAB'],array['Nairobi','Kisumu','Mombasa'],true,250,3,true,1)
on conflict(program_id,version) do nothing;
insert into public.clinic_enrollments(clinic_organization_id,program_id,active,approved_at) values
 ('20000000-0000-4000-8000-000000000001','40000000-0000-4000-8000-000000000001',true,now()),
 ('20000000-0000-4000-8000-000000000002','40000000-0000-4000-8000-000000000001',true,now())
on conflict(clinic_organization_id,program_id) do nothing;
insert into public.registered_devices(id,clinic_organization_id,device_fingerprint_hash,device_name,active,last_seen_at) values
 ('50000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001',encode(extensions.digest('NENA-SYNTHETIC-DEVICE-001','sha256'),'hex'),'Mwangaza Demo Tablet',true,now()),
 ('50000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002',encode(extensions.digest('NENA-SYNTHETIC-DEVICE-002','sha256'),'hex'),'Lakeview Demo Tablet',true,now())
on conflict(id) do nothing;
insert into public.patient_tokens(id,program_id,patient_ref_hash,coverage_status,valid_from,valid_until) values
 ('60000000-0000-4000-8000-000000000001','40000000-0000-4000-8000-000000000001',encode(extensions.digest('NENA-DEMO-PATIENT-001','sha256'),'hex'),'active',now()-interval '1 day',now()+interval '1 year'),
 ('60000000-0000-4000-8000-000000000002','40000000-0000-4000-8000-000000000001',encode(extensions.digest('NENA-DEMO-PATIENT-002','sha256'),'hex'),'active',now()-interval '1 day',now()+interval '1 year')
on conflict(id) do nothing;
-- Auth users and org_memberships are intentionally not seeded. Create users via Supabase Auth,
-- then assign memberships through a trusted administrative process.
