WITH cur AS (
    SELECT CASE
        WHEN pg_is_in_recovery() THEN COALESCE(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn())
        ELSE pg_current_wal_lsn()
    END AS cur_lsn
)
SELECT
    s.slot_name,
    s.slot_type,
    CASE WHEN s.active THEN 1 ELSE 0 END AS active,
    COALESCE(s.active_pid, 0) AS active_pid,
    COALESCE(s.database, '') AS database,
    COALESCE(s.restart_lsn::text, '') AS restart_lsn,
    COALESCE(s.confirmed_flush_lsn::text, '') AS confirmed_flush_lsn,
    COALESCE(s.wal_status, 'unknown') AS wal_status,
    COALESCE(s.safe_wal_size, -1)::bigint AS safe_wal_size_bytes,
    CASE
        WHEN s.restart_lsn IS NULL OR cur.cur_lsn IS NULL THEN 0
        ELSE GREATEST(pg_wal_lsn_diff(cur.cur_lsn, s.restart_lsn)::bigint, 0)
    END AS retained_wal_bytes
FROM pg_replication_slots s
CROSS JOIN cur
ORDER BY s.slot_name;
