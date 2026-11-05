-- Run after schema and import in a disposable PostgreSQL database.
-- Each invalid write must fail inside a PL/pgSQL subtransaction.
\set ON_ERROR_STOP on
DO $$
BEGIN
    BEGIN
        INSERT INTO branches SELECT * FROM branches LIMIT 1;
        RAISE EXCEPTION 'FAIL: duplicate PK accepted';
    EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'PASS duplicate PK'; END;
    BEGIN
        INSERT INTO transactions VALUES (999999999,999999999,'2026-01-01T10:00:00-05:00');
        RAISE EXCEPTION 'FAIL: orphan FK accepted';
    EXCEPTION WHEN foreign_key_violation THEN RAISE NOTICE 'PASS orphan FK'; END;
    BEGIN
        UPDATE ingredients SET package_size=-1 WHERE ingredient_id=1;
        RAISE EXCEPTION 'FAIL: negative package accepted';
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'PASS negative package'; END;
    BEGIN
        UPDATE transaction_items SET fulfilled_qty=requested_qty+1 WHERE transaction_item_id=1;
        RAISE EXCEPTION 'FAIL: overfulfilled item accepted';
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'PASS overfulfilled item'; END;
    BEGIN
        UPDATE inventory_snapshots SET closing_stock=closing_stock+1 WHERE snapshot_id=1;
        RAISE EXCEPTION 'FAIL: conservation violation accepted';
    EXCEPTION WHEN check_violation THEN RAISE NOTICE 'PASS conservation'; END;
    BEGIN
        DELETE FROM ingredients WHERE ingredient_id=1;
        RAISE EXCEPTION 'FAIL: referenced ingredient deleted';
    EXCEPTION WHEN foreign_key_violation OR restrict_violation THEN RAISE NOTICE 'PASS restrict deletion'; END;
END $$;
SELECT 'PASS all SQL constraints tested' AS result;
