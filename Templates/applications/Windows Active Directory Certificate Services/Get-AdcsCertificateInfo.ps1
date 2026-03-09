param(
    [Parameter(Mandatory = $true)]
    [string]$Thumbprint
)

$stores = @(
    'Cert:\LocalMachine\My',
    'Cert:\LocalMachine\WebHosting',
    'Cert:\LocalMachine\CA'
)

$normalizedThumbprint = ($Thumbprint -replace '[^A-Fa-f0-9]', '').ToUpperInvariant()

$cert = $null
$foundStore = $null

foreach ($store in $stores) {
    $candidate = Get-ChildItem -Path $store -ErrorAction SilentlyContinue |
        Where-Object { $_.Thumbprint -eq $normalizedThumbprint } |
        Select-Object -First 1

    if ($null -ne $candidate) {
        $cert = $candidate
        $foundStore = $store
        break
    }
}

if ($null -eq $cert) {
    [PSCustomObject]@{
        found          = 0
        thumbprint     = $normalizedThumbprint
        subject        = ''
        issuer         = ''
        store          = ''
        not_after      = ''
        days_remaining = 0
    } | ConvertTo-Json -Compress
    exit 0
}

$daysRemaining = [math]::Floor(($cert.NotAfter.ToUniversalTime() - [datetime]::UtcNow).TotalDays)

[PSCustomObject]@{
    found          = 1
    thumbprint     = [string]$cert.Thumbprint
    subject        = [string]$cert.Subject
    issuer         = [string]$cert.Issuer
    store          = [string]$foundStore
    not_after      = $cert.NotAfter.ToString('o')
    days_remaining = $daysRemaining
} | ConvertTo-Json -Compress
