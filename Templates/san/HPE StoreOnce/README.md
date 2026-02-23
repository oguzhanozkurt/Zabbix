Host Macros
{$STOREONCE.HOST}

Purpose: StoreOnce appliance management address used for API calls.
What to enter: FQDN or IP address reachable from the Zabbix Server/Proxy (e.g., 10.10.101.210 or storeonce01.company.local).
Notes:

Use the management interface address (not a data/replication-only network).

Ensure DNS resolution is available if you use an FQDN.

{$STOREONCE.PORT}

Purpose: HTTPS port for the StoreOnce REST API endpoint.
What to enter: Typically 443.
Notes:

Change only if your environment uses a non-standard HTTPS port.

{$STOREONCE.USER}

Purpose: Username for StoreOnce API authentication.
What to enter: A StoreOnce user account with sufficient privileges to read cluster status, hardware inventory, and resource monitoring metrics.
Recommended role: A read-only / monitoring-oriented account when possible.
Notes:

The account must be allowed to access the StoreOnce REST API endpoints used by this template.

{$STOREONCE.PASS}

Purpose: Password for the StoreOnce API authentication.
What to enter: The password for {$STOREONCE.USER}.
Security: Store this as a Secret macro in Zabbix to avoid exposing credentials.
Notes:

If credentials change, update this macro and re-check item status.

{$STOREONCE.NODE}

Purpose: Cluster node index used by resourceMonitoring endpoints (CPU/Memory).
What to enter: 1 for most StoreOnce Gen3 (3.x) systems.
Notes:

Some StoreOnce installations return “Zero is not a valid node number” when node 0 is used.

If resourceMonitoring items return empty payloads, verify the correct node index by testing the endpoint manually and adjust this value accordingly.

{$STOREONCE_CPU_WINDOW_MIN}

Purpose: Time window (in minutes) used to query CPU metrics from the StoreOnce resourceMonitoring API.
What to enter: A positive integer, e.g., 15, 30, or 60.
How it’s used: The template queries a rolling time range (end = now, start = now − window) and extracts the most recent datapoint.
Notes:

If the CPU endpoint returns empty results, increase this value (e.g., from 15 to 60) to broaden the sampling window.

Keep the window reasonable to avoid unnecessary payload size.

Optional (Recommended) Macros
{$STOREONCE_MEM_WINDOW_MIN} (optional)

Purpose: Time window (in minutes) used to query Memory metrics from the StoreOnce resourceMonitoring API.
What to enter: Same approach as CPU (e.g., 60).
Default behavior: If not defined, the template falls back to {$STOREONCE_CPU_WINDOW_MIN}.
Notes:

Define this macro if you want a different sampling window for memory compared to CPU.

Connectivity and Security Notes (README section suggestion)

Ensure the StoreOnce HTTPS endpoint is reachable from the Zabbix Server/Proxy, not from the Zabbix frontend.

If the StoreOnce appliance uses a self-signed certificate, you may need to trust the certificate on the Zabbix Server/Proxy OS, depending on the item type (HTTP Agent vs Script).

Use a dedicated monitoring account with least-privilege permissions whenever possible.
