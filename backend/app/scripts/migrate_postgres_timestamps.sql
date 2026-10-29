-- Run once for databases created before the timezone-aware model fix:
-- docker exec -i gaudi-postgres psql -U gaudi -d and_you -v ON_ERROR_STOP=1 < backend/app/scripts/migrate_postgres_timestamps.sql
-- Existing naive timestamps were written as UTC. Re-running is safe.
BEGIN;
DO $$
DECLARE
    col record;
BEGIN
    FOR col IN
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name IN (
              'coding_test_problems', 'coding_test_submissions',
              'cs_eval_questions', 'cs_eval_sessions'
          )
          AND column_name IN ('created_at', 'updated_at')
          AND data_type = 'timestamp without time zone'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ALTER COLUMN %I TYPE timestamptz USING %I AT TIME ZONE ''UTC''',
            col.table_schema, col.table_name, col.column_name, col.column_name
        );
    END LOOP;
END $$;
COMMIT;
