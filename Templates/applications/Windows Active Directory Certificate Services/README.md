# Windows AD CS Certificate Monitoring by Zabbix Agent (PowerShell)

This repository provides a custom Zabbix template to monitor a **Microsoft AD CS–issued certificate** installed on a **Windows host**.  
The solution uses a **Zabbix Agent / Agent 2 UserParameter** that executes a PowerShell script, returns **JSON**, and then extracts values via **dependent items**.

- Template: **Windows AD CS certificate by Zabbix agent**
- Zabbix export: **7.0**
- Components:
  - `Windows AD CS certificate by Zabbix agent.yaml`
  - `Get-AdcsCertificateInfo.ps1`

> Note: This is a community template and is not an official Microsoft release.

---

## What’s Included

### Certificate Inventory (JSON → Dependent Items)
- Certificate **subject**
- Certificate **issuer**
- Certificate **store** (where the certificate was found)
- Certificate **expiry date** (`NotAfter`) in ISO 8601 format
- **Days remaining** until expiry
- **Presence state** (found / not found)

### Triggers
- Certificate **not found** (DISASTER)
- **No data** received from master item (DISASTER)
- Expiration **warning** (HIGH) and **critical** (DISASTER) based on thresholds

---

## How It Works (High Level)

1. Zabbix calls the agent key: `cert.info[<thumbprint>]`
2. The Windows agent runs `Get-AdcsCertificateInfo.ps1` with the thumbprint parameter
3. The script returns a compact JSON payload:
   - `found`, `thumbprint`, `subject`, `issuer`, `store`, `not_after`, `days_remaining`
4. Dependent items extract fields using JSONPath
5. Triggers evaluate presence, nodata, and expiration thresholds

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Windows host:
  - **Zabbix Agent 2** (recommended) or **Zabbix Agent**
  - PowerShell available
- Permissions:
  - The agent service account must be able to read the certificate store (typically OK for LocalMachine stores)
- Network access:
  - Zabbix → Windows agent port (10050 for passive, 10051 for active via server)

---

## Quick Start

### 1) Deploy the PowerShell Script
Copy `Get-AdcsCertificateInfo.ps1` to the Windows host, for example:

- **Zabbix Agent 2 (default path):**  
  `C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1`

> If you use Zabbix Agent (classic), adjust the path accordingly.

### 2) Add the UserParameter
Edit your agent configuration file and add:

```ini
UserParameter=cert.info[*],powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1" -Thumbprint "$1"

3) Restart Zabbix Agent Service

Restart Zabbix Agent 2 service on the host.

4) Import the Template

Zabbix UI → Data collection → Templates → Import
Import: Windows AD CS certificate by Zabbix agent.yaml

5) Link Template to Host

Link the template to the Windows host that holds the certificate.

6) Configure Host Macros

Set at host level:

Macro	Default	Description
{$CERT.THUMBPRINT}	CHANGE_ME	Thumbprint of the certificate to monitor
{$CERT.WARN.DAYS}	30	Warning threshold in days before expiration
{$CERT.CRIT.DAYS}	7	Critical threshold in days before expiration
{$CERT.NODATA}	12h	Nodata period for the master item
Finding the Certificate Thumbprint

Run on the Windows host:

Get-ChildItem Cert:\LocalMachine\My |
Select-Object Subject, Thumbprint, NotAfter

Tip: If you paste thumbprints with spaces or hidden characters, the script normalizes the input to hex-only (A–F/0–9).

Monitored Items (Summary)
Master Item

AD CS certificate raw info
Key: cert.info[{$CERT.THUMBPRINT}]
Type: Zabbix agent (passive)
Interval: 1h
History: 7d
Value type: Text (JSON)

Dependent Items

adcs.cert.found — 1 if found, else 0

adcs.cert.days_remaining — days remaining until expiry

adcs.cert.subject

adcs.cert.issuer

adcs.cert.not_after

adcs.cert.store

Triggers (Summary)

AD CS certificate: Certificate not found (DISASTER)
Fires when the certificate matching {$CERT.THUMBPRINT} cannot be located.

AD CS certificate: No data received (DISASTER)
Fires when master item has no data for {$CERT.NODATA}.

AD CS certificate: Expiration warning (HIGH)
Fires when days remaining < {$CERT.WARN.DAYS} and >= {$CERT.CRIT.DAYS}.

AD CS certificate: Expiration is critical (DISASTER)
Fires when days remaining < {$CERT.CRIT.DAYS}.

Script Behavior (Default)

By default, the script searches these certificate stores:

Cert:\LocalMachine\My

Cert:\LocalMachine\WebHosting

Cert:\LocalMachine\CA

If your certificate is stored elsewhere, you can extend the $stores list in the script.

Validation & Troubleshooting
Test the Script Locally

On the Windows host:

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\Zabbix Agent 2\scripts\Get-AdcsCertificateInfo.ps1" -Thumbprint "<THUMBPRINT>"

Expected output: a single-line JSON, e.g. {"found":1,...}.

Test via Zabbix Agent

On Zabbix server/proxy:

zabbix_get -s <WINDOWS_HOST_IP> -k "cert.info[<THUMBPRINT>]"
If you see “No data received”

Confirm the UserParameter line is loaded (agent restarted, correct config file).

Verify the script path exists and the agent service account can read it.

Confirm PowerShell execution is permitted for the agent service context.

Validate that your monitored thumbprint exists in one of the scanned stores.

If the certificate is “not found”

Confirm the thumbprint is correct (no wrong certificate store / wrong cert).

Verify the certificate is installed under LocalMachine (not CurrentUser).

Extend the $stores array in the script if needed.

Notes / Compatibility

The template is built around Zabbix Agent 2 and passive checks by default.

If your environment uses active checks only, change the master item type after import to ZABBIX_ACTIVE.

If you use Zabbix Agent (classic), update the script path in the UserParameter accordingly.

Security Notes

The UserParameter uses -ExecutionPolicy Bypass. Keep exposure low by:

Restricting who can edit the agent configuration

Restricting agent access (firewall allow-lists, network segmentation)

Ensuring the script directory is writable only by administrators

Contributing

Contributions are welcome, including:

Adding additional certificate stores or enhanced matching logic

Multi-certificate monitoring (LLD-based approach)

Additional triggers (e.g., issuer mismatch, subject mismatch)

Please include:

Zabbix version

Windows version

Sanitized sample JSON output

Expected vs. actual behavior

License

Add a LICENSE file to define reuse/redistribution rights (e.g., MIT / Apache-2.0 / GPL-3.0).

Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Microsoft.
