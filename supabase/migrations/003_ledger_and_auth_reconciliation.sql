-- ============================================================================
-- NENA AI | MIGRATION 003: LEDGER RECONCILIATION & ATOMIC AUTHORIZATION ENGINE
-- ============================================================================
-- Corrects Phase 2 column and enum mismatches against Phase 1 schema.
-- Reconciles:
--   1. event_type = 'subsidy_authorized' (matches public.ledger_event_type enum)
--   2. Removes nonexistent 'status' column from ledger_entries writes
--   3. Implements atomic row-level reservation and concurrent overspend guard
--   4. Adds cryptographic chain verification procedure: verify_ledger_chain()
--   5. Adds compensating reversal event procedure: reverse_ledger_entry()
-- ============================================================================

CREATE OR REPLACE FUNCTION public.authorize_encounter(p_encounter_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    e care_encounters%ROWTYPE;
    p funding_programs%ROWTYPE;
    existing_ledger ledger_entries%ROWTYPE;
    new_ledger ledger_entries%ROWTYPE;
    new_payout payouts%ROWTYPE;
    committed NUMERIC(18,2);
    passed_count INTEGER;
    risk anomaly_assessments%ROWTYPE;
BEGIN
    -- 1. Lock encounter record for update
    SELECT * INTO e
    FROM care_encounters
    WHERE id = p_encounter_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Encounter not found' USING ERRCODE = 'P0002';
    END IF;

    -- 2. Check if already authorized (idempotent guard)
    SELECT * INTO existing_ledger
    FROM ledger_entries
    WHERE encounter_id = p_encounter_id
      AND event_type = 'subsidy_authorized'
    LIMIT 1;

    IF FOUND THEN
        SELECT * INTO new_payout
        FROM payouts
        WHERE ledger_entry_id = existing_ledger.id;

        RETURN jsonb_build_object(
            'ledger_id', existing_ledger.id,
            'payout_id', new_payout.id,
            'already_authorized', TRUE,
            'tx_hash', existing_ledger.tx_hash
        );
    END IF;

    -- 3. Verify clinical encounter state
    IF e.status NOT IN ('pending_verification', 'approved') THEN
        RAISE EXCEPTION 'Encounter is not eligible for authorization: current status %', e.status USING ERRCODE = '23514';
    END IF;

    -- 4. Lock funding program row FOR UPDATE to serialize fund reservation
    SELECT * INTO p
    FROM funding_programs
    WHERE id = e.program_id
    FOR UPDATE;

    IF NOT FOUND OR NOT p.active THEN
        RAISE EXCEPTION 'Funding program inactive or missing' USING ERRCODE = '23514';
    END IF;

    IF NOW() < p.starts_at OR (p.ends_at IS NOT NULL AND NOW() > p.ends_at) THEN
        RAISE EXCEPTION 'Funding program is outside its active operational date range' USING ERRCODE = '23514';
    END IF;

    IF e.currency <> p.currency THEN
        RAISE EXCEPTION 'Currency mismatch: encounter uses % but program requires %', e.currency, p.currency USING ERRCODE = '23514';
    END IF;

    -- 5. Enforce all four verification stages
    SELECT COUNT(DISTINCT stage) INTO passed_count
    FROM verification_events
    WHERE encounter_id = p_encounter_id
      AND status = 'passed'
      AND stage IN ('identity_device','patient_consent','program_policy','anomaly_detection');

    IF passed_count <> 4 THEN
        RAISE EXCEPTION 'All four verification stages must pass (passed % of 4)', passed_count USING ERRCODE = '23514';
    END IF;

    -- 6. Enforce anomaly assessment outcome
    SELECT * INTO risk
    FROM anomaly_assessments
    WHERE encounter_id = p_encounter_id
    ORDER BY created_at DESC
    LIMIT 1;

    IF NOT FOUND OR risk.recommended_action <> 'approve' THEN
        RAISE EXCEPTION 'Anomaly assessment does not permit automatic authorization' USING ERRCODE = '23514';
    END IF;

    -- 7. Compute total committed capital and prevent concurrent overspend
    SELECT COALESCE(SUM(
        CASE
            WHEN event_type = 'subsidy_authorized' THEN amount
            WHEN event_type = 'reversal' THEN -amount
            ELSE 0
        END
    ), 0)
    INTO committed
    FROM ledger_entries
    WHERE program_id = e.program_id;

    IF committed + e.amount > p.allocated_amount THEN
        RAISE EXCEPTION 'Insufficient uncommitted program funds: committed % + claim % exceeds allocated %',
            committed, e.amount, p.allocated_amount USING ERRCODE = '23514';
    END IF;

    -- 8. Append immutable financial ledger entry (trigger trg_ledger_hash populates prev_hash & tx_hash)
    INSERT INTO ledger_entries (
        encounter_id,
        program_id,
        clinic_organization_id,
        funder_organization_id,
        event_type,
        amount,
        currency,
        metadata
    ) VALUES (
        e.id,
        e.program_id,
        e.clinic_organization_id,
        p.funder_organization_id,
        'subsidy_authorized',
        e.amount,
        e.currency,
        jsonb_build_object(
            'authorization_source', 'nena-fastapi',
            'risk_score', risk.risk_score,
            'risk_level', risk.risk_level,
            'authorized_at', now()
        )
    ) RETURNING * INTO new_ledger;

    -- 9. Insert initialized payout projection record
    INSERT INTO payouts (
        ledger_entry_id,
        provider,
        amount,
        currency,
        status
    ) VALUES (
        new_ledger.id,
        'MPESA_MOCK',
        e.amount,
        e.currency,
        'initiated'
    ) RETURNING * INTO new_payout;

    -- 10. Advance care encounter state to settlement_pending
    UPDATE care_encounters
    SET status = 'settlement_pending'
    WHERE id = e.id;

    RETURN jsonb_build_object(
        'ledger_id', new_ledger.id,
        'payout_id', new_payout.id,
        'already_authorized', FALSE,
        'tx_hash', new_ledger.tx_hash,
        'amount', new_ledger.amount,
        'currency', new_ledger.currency
    );
END;
$$;

-- Grant execution to service_role only
REVOKE ALL ON FUNCTION public.authorize_encounter(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.authorize_encounter(UUID) FROM anon;
REVOKE ALL ON FUNCTION public.authorize_encounter(UUID) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.authorize_encounter(UUID) TO service_role;

-- ============================================================================
-- CRYPTOGRAPHIC LEDGER CHAIN VERIFICATION FUNCTION
-- ============================================================================
CREATE OR REPLACE FUNCTION public.verify_ledger_chain()
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions, pg_temp
AS $$
DECLARE
    entry RECORD;
    computed_hash TEXT;
    expected_prev TEXT := repeat('0', 64);
    canonical_payload TEXT;
    inconsistencies JSONB := '[]'::jsonb;
    entry_count INTEGER := 0;
BEGIN
    FOR entry IN
        SELECT *
        FROM public.ledger_entries
        ORDER BY created_at ASC, id ASC
    LOOP
        entry_count := entry_count + 1;

        -- 1. Verify previous hash chaining
        IF entry.prev_hash <> expected_prev THEN
            inconsistencies := inconsistencies || jsonb_build_object(
                'entry_id', entry.id,
                'error', 'PREV_HASH_MISMATCH',
                'expected_prev', expected_prev,
                'found_prev', entry.prev_hash
            );
        END IF;

        -- 2. Recalculate canonical payload digest
        canonical_payload := jsonb_build_object(
            'id', entry.id,
            'encounter_id', entry.encounter_id,
            'program_id', entry.program_id,
            'clinic_organization_id', entry.clinic_organization_id,
            'funder_organization_id', entry.funder_organization_id,
            'event_type', entry.event_type,
            'amount', entry.amount,
            'currency', entry.currency,
            'prev_hash', entry.prev_hash,
            'metadata', entry.metadata,
            'created_by', entry.created_by,
            'created_at', entry.created_at
        )::text;

        computed_hash := encode(extensions.digest(convert_to(canonical_payload, 'UTF8'), 'sha256'), 'hex');

        -- 3. Verify current tx_hash matches digest
        IF entry.tx_hash <> computed_hash THEN
            inconsistencies := inconsistencies || jsonb_build_object(
                'entry_id', entry.id,
                'error', 'TX_HASH_CORRUPTION',
                'expected_tx', computed_hash,
                'found_tx', entry.tx_hash
            );
        END IF;

        expected_prev := entry.tx_hash;
    END LOOP;

    RETURN jsonb_build_object(
        'verified', (jsonb_array_length(inconsistencies) = 0),
        'total_entries', entry_count,
        'current_head_hash', expected_prev,
        'inconsistencies', inconsistencies
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.verify_ledger_chain() TO service_role;
GRANT EXECUTE ON FUNCTION public.verify_ledger_chain() TO authenticated;

-- ============================================================================
-- COMPENSATING REVERSAL PROCEDURE
-- ============================================================================
CREATE OR REPLACE FUNCTION public.reverse_ledger_entry(
    p_ledger_id UUID,
    p_reason TEXT,
    p_actor_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    orig ledger_entries%ROWTYPE;
    rev ledger_entries%ROWTYPE;
BEGIN
    SELECT * INTO orig
    FROM ledger_entries
    WHERE id = p_ledger_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Original ledger entry not found' USING ERRCODE = 'P0002';
    END IF;

    IF orig.event_type = 'reversal' THEN
        RAISE EXCEPTION 'Cannot reverse an existing reversal entry' USING ERRCODE = '23514';
    END IF;

    INSERT INTO ledger_entries (
        encounter_id,
        program_id,
        clinic_organization_id,
        funder_organization_id,
        event_type,
        amount,
        currency,
        metadata,
        created_by
    ) VALUES (
        orig.encounter_id,
        orig.program_id,
        orig.clinic_organization_id,
        orig.funder_organization_id,
        'reversal',
        orig.amount,
        orig.currency,
        jsonb_build_object(
            'reversed_ledger_id', orig.id,
            'reason', p_reason,
            'actor_id', p_actor_id,
            'reversed_at', now()
        ),
        p_actor_id
    ) RETURNING * INTO rev;

    RETURN jsonb_build_object(
        'reversal_ledger_id', rev.id,
        'reversed_original_id', orig.id,
        'tx_hash', rev.tx_hash,
        'restored_amount', rev.amount
    );
END;
$$;

GRANT EXECUTE ON FUNCTION public.reverse_ledger_entry(UUID, TEXT, UUID) TO service_role;
