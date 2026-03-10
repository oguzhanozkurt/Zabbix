# Veritas Event ID Monitoring (Zabbix Template)

This repository provides a Zabbix template to monitor **Arctera/Veritas Enterprise Vault** health by detecting **specific Windows Event IDs** in the Enterprise Vault event logs.

- Template name: **Veritas Event ID Monitoring**
- Zabbix export: **7.0**
- File: `Veritas Event ID Monitoring.yaml`
- Collection method: **Zabbix Agent (Active)** → `eventlog[]` (LOG items) → triggers based on `logeventid()`

> Note: This is a community template and is not an official Veritas/Arctera release.

---

## What’s Included

### Windows Event Log Monitoring (Active Checks)
The template monitors events in the following Windows event logs (depending on your product/version):
- **Arctera Enterprise Vault**
- **Veritas Enterprise Vault**

Each monitored Event ID is collected as a **LOG** item via Zabbix **active checks** (`ZABBIX_ACTIVE`) and evaluated by trigger rules.

### Alerting Model
- Most triggers create a **problem** when the specified Event ID is detected.
- Many triggers are configured with **Manual close = YES** (operator-driven closure).
- Some events are modeled as **problem/resolved pairs** using recovery expressions (e.g., “Service stopped” vs “Service resolved”).

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Windows host running Enterprise Vault components
- Zabbix Agent installed on the Windows host and configured for **Active checks**
- The agent service account must have permissions to read the monitored event logs
  - If required, add the service account to **Event Log Readers**.
- Network access:
  - Windows Agent → Zabbix Server/Proxy (10051) for active check delivery

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Veritas Event ID Monitoring.yaml`

### 2) Link the Template to the Windows Host
Link the template to the Windows host where Enterprise Vault services run.

### 3) Ensure Zabbix Agent Active Checks are Enabled
On the Windows host, confirm your agent config includes (examples):

~~~ini
ServerActive=<ZABBIX_SERVER_OR_PROXY_IP>
Hostname=<EXACT_HOSTNAME_AS_IN_ZABBIX>
~~~

Restart the agent service after changes.

### 4) Validate the Enterprise Vault Event Log Exists
On the Windows host (PowerShell):

~~~powershell
Get-WinEvent -ListLog * | Where-Object {$_.LogName -match "Enterprise Vault"} |
Select-Object LogName, RecordCount, IsEnabled
~~~

If the log name differs in your environment, adjust the template item keys accordingly.

---

## Monitored Event IDs (Overview)

The template includes LOG items (active) for a set of Enterprise Vault–related Event IDs. Examples covered include:

### Disk Space / Storage
- **4141 / 4142 / 4143** — Insufficient Disk Space
- **4145 / 4146 / 4147** — Out Of Disk Space
- **2851** — Not enough free disk space to continue
- **29005** — Storage queue location is not accessible
- **29013** — Item not added to storage queue due to disk space threshold

### Services / Tasks / Controllers
- **3290** — Task Controller Service stopped *(recovered by 3289)*
- **3289** — Task Controller Service resolved
- **3295** — Journal Task stopped *(recovered by 3298 if enabled)*
- **3298** — Journal Task resolved *(may be disabled in the template export)*
- **4111** — Admin Service stopped *(recovered by 4110)*
- **4110** — Admin Service resolved
- **6222** — Storage Service stopped *(recovered by 6221 if enabled)*
- **6221** — Storage Service resolved *(may be disabled in the template export)*
- **7169** — Indexing Service has stopped

### Mailbox / Journal / Exchange Integration
- **3229** — Journal mailbox has a backlog *(recovered by 3228)*
- **3228** — Journal mailbox resolved
- **2247** — Error while processing Journal mailbox; mailbox disabled/suspended; task shuts down
- **2258** — Journal Task could not be started due to startup errors
- **2259** — Could not open mailbox; mailbox will not be processed
- **3039** — Could not get a MAPI session from the pool
- **2209** — Failed to initialize the MAPI subsystem
- **2210** — Failed to initialize the COM subsystem
- **3460** — Task failed to log on to Exchange server
- **41447** — Exchange mailbox sync not working *(recovered by 41446)*
- **41446** — Exchange mailbox synchronization has resolved

### Database / Platform Errors
- **13360** — Error accessing the Vault Database

### Unscheduled Tasks
- **41286** — Unscheduled tasks *(recovered by 41285)*
- **41285** — Unscheduled tasks resolved

> Tip: Some “resolved” items are included as LOG collectors but may be **disabled** in the export. If you want full auto-recovery, ensure the corresponding “resolved” items are enabled.

---

## How It Works

### Item Collection
Each monitored Event ID is collected using the Zabbix key:

- `eventlog["<EnterpriseVaultLogName>",,,,<EventIDOrRegex>,,skip]`

Key points:
- **Active checks** are used (agent pushes results).
- `skip` mode ensures Zabbix starts from the most recent position and processes new events forward.

### Trigger Evaluation
Triggers use `logeventid()` to open a problem when a new matching event is detected.

Some triggers implement **recovery expressions**, for example:
- “Service stopped” closes when “Service resolved” is observed.
- “Backlog” closes when “Backlog resolved” is observed.

---

## Validation & Troubleshooting

### Verify an Event ID Exists in the Log (PowerShell)
Example: check last 5 occurrences of EventID 4146 in the Arctera log:

~~~powershell
Get-WinEvent -LogName "Arctera Enterprise Vault" -FilterHashtable @{Id=4146} -MaxEvents 5 |
Select-Object TimeCreated, Id, LevelDisplayName, Message
~~~

If your log name is different (e.g., `Veritas Enterprise Vault`), replace `-LogName` accordingly.

### If You Receive No Data in Zabbix
- Confirm the host is configured for **active checks** (`ServerActive`, `Hostname`).
- Confirm the agent can read the target log(s) (permissions / Event Log Readers).
- Confirm the event log names match the template keys exactly.
- Check agent logs for eventlog access errors.

### If Problems Do Not Auto-Recover
- Verify that the corresponding “resolved” Event ID item is **enabled**.
- Verify that “resolved” events are actually being generated in your environment.

---

## Security Notes

- Event logs may contain sensitive operational information.
- Restrict access by applying:
  - Source IP allow-lists / firewall rules for Zabbix ports
  - Role-based access control in Zabbix
  - Least-privilege permissions for the agent service account

---

## Contributing

Contributions are welcome, including:
- Adding/removing Event IDs based on operational requirements
- Extending recovery pairs (problem/resolved)
- Adjusting polling intervals and retention
- Documentation improvements and validated event mappings

Please include:
- Enterprise Vault version (Veritas/Arctera)
- Windows version
- Zabbix version
- Sanitized event samples (Event ID + message excerpt)

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Veritas or Arctera.
