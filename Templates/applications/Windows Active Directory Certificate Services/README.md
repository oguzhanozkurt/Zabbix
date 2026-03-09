# Windows AD CS Certificate Monitoring by Zabbix Agent (PowerShell)

This repository provides a custom Zabbix template to monitor a **Microsoft AD CS–issued certificate** installed on a **Windows host**.
The solution uses a **Zabbix Agent / Agent 2 UserParameter** that executes a PowerShell script, returns **JSON**, and extracts values via **dependent items**.

- Template: **Windows AD CS certificate by Zabbix agent**
- Zabbix export: **7.0**
- Files:
  - `Windows AD CS certificate by Zabbix agent.yaml`
  - `Get-AdcsCertificateInfo.ps1`

> Note: This is a community template and is not an official Microsoft release.

---

## What’s Included

### Certificate Data (JSON → Dependent Items)
- Certificate **subject**
- Certificate **issuer**
- Certificate **store** (where the certificate was found)
- Certificate **expiry date** (`not_after`) in ISO 8601 format
- **Days remaining** until expiry
- **Presence state** (found / not found)

### Triggers
- Certificate **not found** (DISASTER)
- **No data** received from master item (DISASTER)
- Expiration **warning** (HIGH) and **critical** (DISASTER) based on thresholds

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Windows host:
  - **Zabbix Agent 2** (recommended) or **Zabbix Agent**
  - PowerShell available
- Permissions:
  - The agent service account must be able to read the certificate store (typically OK for LocalMachine stores)
- Connectivity:
  - Zabbix → Windows agent (10050 for passive checks)

---

## Quick Start

### 1) Deploy the PowerShell Script
Copy `Get-AdcsCertificateInfo.ps1` to the Windows host, for example:

- **Zabbix Agent 2 scripts folder:**
  `C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1`

> If you use Zabbix Agent (classic), adjust paths accordingly.

### 2) Add the UserParameter
Recommended approach: create a dedicated config snippet file:

- `C:\Program Files\Zabbix Agent 2\zabbix_agent2.d\adcs_cert.conf`

Add the following line:

~~~ini
UserParameter=cert.info[*],powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1" -Thumbprint "$1"
~~~

> Alternatively, you can place the same line into `zabbix_agent2.conf`, but keeping it in `zabbix_agent2.d\` is cleaner.

### 3) Restart Zabbix Agent Service
Restart **Zabbix Agent 2** on the host:

~~~powershell
Restart-Service "Zabbix Agent 2"
~~~

(Alternative)

~~~cmd
net stop "Zabbix Agent 2" && net start "Zabbix Agent 2"
~~~

### 4) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Windows AD CS certificate by Zabbix agent.yaml`

### 5) Link Template to Host
Link the template to the Windows host that holds the certificate.

### 6) Configure Host Macros
Set at host level:

| Macro | Default | Description |
|------|---------|-------------|
| `{$CERT.THUMBPRINT}` | `CHANGE_ME` | Thumbprint of the certificate to monitor |
| `{$CERT.WARN.DAYS}` | `30` | Warning threshold in days before expiration |
| `{$CERT.CRIT.DAYS}` | `7` | Critical threshold in days before expiration |
| `{$CERT.NODATA}` | `12h` | Nodata period for the master item |

---

## Finding the Certificate Thumbprint

Run on the Windows host:

~~~powershell
Get-ChildItem Cert:\LocalMachine\My |
Select-Object Subject, Thumbprint, NotAfter
~~~

> Tip: If you paste thumbprints with spaces or hidden characters, the script normalizes the input to hex-only (A–F/0–9).

---

## How It Works

1. Zabbix polls: `cert.info[{$CERT.THUMBPRINT}]`
2. Agent runs `Get-AdcsCertificateInfo.ps1 -Thumbprint "<...>"`
3. Script returns JSON:
   - `found`, `thumbprint`, `subject`, `issuer`, `store`, `not_after`, `days_remaining`
4. Dependent items extract fields via JSONPath
5. Triggers evaluate presence, nodata, and expiry thresholds

---

## Script Behavior (Default)

By default, the script searches these certificate stores:
- `Cert:\LocalMachine\My`
- `Cert:\LocalMachine\WebHosting`
- `Cert:\LocalMachine\CA`

If your certificate is stored elsewhere, extend the `$stores` list in the script.

---

## Validation & Troubleshooting

### Test the Script Locally
On the Windows host:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1" -Thumbprint "<THUMBPRINT>"
~~~

Expected output: a single-line JSON, e.g. `{"found":1,...}`.

### Test via Zabbix Agent
From your Zabbix server/proxy:

~~~bash
zabbix_get -s <WINDOWS_HOST_IP> -k "cert.info[<THUMBPRINT>]"
~~~

### If you see “No data received”
- Confirm the UserParameter file is loaded (agent restarted, correct include directory).
- Verify the script path exists and the agent service account can read it.
- Confirm PowerShell execution works under the agent service context.
- Validate that the monitored thumbprint exists in one of the scanned stores.

### If the certificate is “not found”
- Confirm the thumbprint is correct.
- Verify the certificate is installed under **LocalMachine** (not CurrentUser).
- Extend the `$stores` array in the script if needed.

---

## Security Notes

- The UserParameter uses `-ExecutionPolicy Bypass`. Keep exposure low by:
  - Restricting who can edit the agent configuration
  - Restricting agent access (firewall allow-lists, network segmentation)
  - Ensuring the script directory is writable only by administrators

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Microsoft.
