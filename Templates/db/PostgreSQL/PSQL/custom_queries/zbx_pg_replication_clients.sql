WITH cur AS (
    SELECT CASE
        WHEN pg_is_in_recovery() THEN COALESCE(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn())
        ELSE pg_current_wal_lsn()
    END AS cur_lsn
)
SELECT
    COALESCE(r.application_name, '') AS application_name,
    COALESCE(r.client_addr::text, '') AS client_addr,
    COALESCE(r.state, 'unknown') AS state,
    COALESCE(r.sync_state, 'unknown') AS sync_state,
    COALESCE(r.sent_lsn::text, '') AS sent_lsn,
    COALESCE(r.write_lsn::text, '') AS write_lsn,
    COALESCE(r.flush_lsn::text, '') AS flush_lsn,
    COALESCE(r.replay_lsn::text, '') AS replay_lsn,
    CASE WHEN cur.cur_lsn IS NULL OR r.sent_lsn IS NULL THEN 0 ELSE GREATEST(pg_wal_lsn_diff(cur.cur_lsn, r.sent_lsn)::bigint, 0) END AS current_to_sent_lag_bytes,
    CASE WHEN r.sent_lsn IS NULL OR r.write_lsn IS NULL THEN 0 ELSE GREATEST(pg_wal_lsn_diff(r.sent_lsn, r.write_lsn)::bigint, 0) END AS sent_to_write_lag_bytes,
    CASE WHEN r.write_lsn IS NULL OR r.flush_lsn IS NULL THEN 0 ELSE GREATEST(pg_wal_lsn_diff(r.write_lsn, r.flush_lsn)::bigint, 0) END AS write_to_flush_lag_bytes,
    CASE WHEN r.flush_lsn IS NULL OR r.replay_lsn IS NULL THEN 0 ELSE GREATEST(pg_wal_lsn_diff(r.flush_lsn, r.replay_lsn)::bigint, 0) END AS flush_to_replay_lag_bytes,
    CASE WHEN cur.cur_lsn IS NULL OR r.replay_lsn IS NULL THEN 0 ELSE GREATEST(pg_wal_lsn_diff(cur.cur_lsn, r.replay_lsn)::bigint, 0) END AS total_replay_lag_bytes,
    COALESCE(EXTRACT(EPOCH FROM r.write_lag)::bigint, 0) AS write_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM r.flush_lag)::bigint, 0) AS flush_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM r.replay_lag)::bigint, 0) AS replay_lag_sec
FROM pg_stat_replication r
CROSS JOIN cur
ORDER BY application_name, client_addr;
