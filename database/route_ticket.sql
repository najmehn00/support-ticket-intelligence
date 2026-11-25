CREATE OR REPLACE FUNCTION route_ticket(
    p_ticket_id UUID,
    p_destination VARCHAR(40)
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_category VARCHAR(30);
    v_expected_destination VARCHAR(40);
    v_log_id UUID;
BEGIN
    SELECT category
    INTO v_category
    FROM tickets
    WHERE id = p_ticket_id
      AND status = 'pending'
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    v_expected_destination := CASE v_category
        WHEN 'billing' THEN 'finance'
        WHEN 'technical' THEN 'technical'
        WHEN 'manual_review' THEN 'manual_review'
        ELSE NULL
    END;

    IF v_expected_destination IS NULL
       OR p_destination <> v_expected_destination THEN
        RETURN FALSE;
    END IF;

    INSERT INTO routing_logs (
        id,
        ticket_id,
        destination,
        routed_at
    )
    VALUES (
        gen_random_uuid(),
        p_ticket_id,
        p_destination,
        NOW()
    )
    ON CONFLICT (ticket_id) DO NOTHING
    RETURNING id INTO v_log_id;

    IF v_log_id IS NULL THEN
        RETURN FALSE;
    END IF;

    UPDATE tickets
    SET status = 'routed',
        routed_at = NOW()
    WHERE id = p_ticket_id
      AND status = 'pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION USING MESSAGE = concat('Ticket status update failed: ', p_ticket_id);
    END IF;

    RETURN TRUE;
END;
$$;
