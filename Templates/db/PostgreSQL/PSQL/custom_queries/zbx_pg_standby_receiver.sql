WITH standby AS (
    SELECT
        CASE WHEN pg_is_in_recovery() THEN 1 ELSE 0 END AS in_recovery,
        pg_last_wal_receive_lsn() AS receive_lsn,
        pg_last_wal_replay_lsn() AS replay_lsn,
        COALESCE(pg_wal_lsn_diff(pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn())::bigint, 0) AS receive_replay_gap_bytes,
        COALESCE(EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())::bigint, -1) AS replay_delay_sec
)
SELECT
    st.in_recovery,
    COALESCE(wr.status, 'missing') AS status,
    COALESCE(wr.slot_name, 'missing') AS slot_name,
    COALESCE(wr.sender_host, 'missing') AS sender_host,
    COALESCE(wr.sender_port, 0) AS sender_port,
    COALESCE(EXTRACT(EPOCH FROM now() - wr.last_msg_receipt_time)::bigint, -1) AS seconds_since_last_msg,
    COALESCE(st.receive_lsn::text, '') AS receive_lsn,
    COALESCE(st.replay_lsn::text, '') AS replay_lsn,
    st.receive_replay_gap_bytes,
    st.replay_delay_sec,
    COALESCE(wr.latest_end_lsn::text, '') AS latest_end_lsn,
    COALESCE(wr.latest_end_time::text, '') AS latest_end_time
FROM standby st
LEFT JOIN pg_stat_wal_receiver wr ON true;
