SELECT
    name,
    setting,
    COALESCE(unit, '') AS unit,
    CASE
        WHEN setting = '-1' THEN -1
        WHEN COALESCE(unit, '') IN ('B','kB','MB','GB','TB') THEN pg_size_bytes(setting || unit)::bigint
        ELSE setting::bigint
    END AS setting_bytes,
    source,
    COALESCE(sourcefile, '') AS sourcefile,
    COALESCE(sourceline, 0) AS sourceline,
    CASE WHEN pending_restart THEN 1 ELSE 0 END AS pending_restart
FROM pg_settings
WHERE name IN ('wal_keep_size','min_wal_size','max_wal_size','max_slot_wal_keep_size')
ORDER BY name;
