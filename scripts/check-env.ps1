#Requires -Version 5.1
<#
.SYNOPSIS
    Checks whether this Windows host can run RAGFlow v0.27.2 with Docker Desktop.

.DESCRIPTION
    Prints a Markdown table of measured values against RAGFlow's documented
    prerequisites (CPU >= 4 cores, RAM >= 16 GB, disk >= 50 GB,
    Docker >= 24.0.0, Docker Compose >= v2.26.1).

    The script does not pull images, start containers or change any setting.

.PARAMETER Drive
    Host drive that stores the Docker Desktop disk image. Default: C.

.PARAMETER Strict
    Return exit code 1 when any check is WARN or FAIL.

.EXAMPLE
    pwsh -File scripts/check-env.ps1 -Drive C
#>
[CmdletBinding()]
param(
    [string]$Drive = "C",
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$script:results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Item,
        [string]$Actual,
        [string]$Required,
        [ValidateSet("PASS", "WARN", "FAIL", "INFO")]
        [string]$Status,
        [string]$Note = ""
    )
    $script:results.Add([pscustomobject]@{
            Item     = $Item
            Actual   = $Actual
            Required = $Required
            Status   = $Status
            Note     = $Note
        })
}

function Get-NumericVersion {
    param([string]$Text)
    if ($Text -match '(\d+)\.(\d+)\.(\d+)') {
        return [version]::new([int]$Matches[1], [int]$Matches[2], [int]$Matches[3])
    }
    return $null
}

# ---------------------------------------------------------------------------
# Host information
# ---------------------------------------------------------------------------
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$cs = Get-CimInstance -ClassName Win32_ComputerSystem
$cpu = Get-CimInstance -ClassName Win32_Processor | Select-Object -First 1
$ramGb = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
$cpuCores = [int]$cpu.NumberOfCores
$cpuThreads = [int]$cpu.NumberOfLogicalProcessors

Add-Result -Item "Operating system" `
    -Actual ("{0} (build {1}, {2})" -f $os.Caption, $os.BuildNumber, $os.OSArchitecture) `
    -Required "Windows 10/11 x64" `
    -Status "PASS"

Add-Result -Item "CPU" `
    -Actual ("{0} / {1} cores / {2} threads" -f $cpu.Name.Trim(), $cpuCores, $cpuThreads) `
    -Required ">= 4 cores" `
    -Status $(if ($cpuCores -ge 4) { "PASS" } else { "FAIL" })

Add-Result -Item "Physical memory" `
    -Actual ("{0} GB" -f $ramGb) `
    -Required ">= 16 GB" `
    -Status $(if ($ramGb -ge 16) { "PASS" } elseif ($ramGb -ge 14) { "WARN" } else { "FAIL" }) `
    -Note $(if ($ramGb -lt 16) { "Below the official recommendation; tune Docker/WSL memory before ingestion." } else { "" })

try {
    $disk = Get-PSDrive -Name $Drive -ErrorAction Stop
    $freeGb = [math]::Round($disk.Free / 1GB, 2)
    $status = if ($freeGb -ge 50) { "PASS" } elseif ($freeGb -ge 30) { "WARN" } else { "FAIL" }
    Add-Result -Item ("Free space on {0}:" -f $Drive) `
        -Actual ("{0} GB" -f $freeGb) `
        -Required ">= 50 GB" `
        -Status $status `
        -Note "RAGFlow image plus Elasticsearch needs roughly 15-20 GB before data."
}
catch {
    Add-Result -Item ("Free space on {0}:" -f $Drive) -Actual "unknown" -Required ">= 50 GB" -Status "FAIL" -Note $_.Exception.Message
}

# ---------------------------------------------------------------------------
# Docker Desktop / engine / compose
# ---------------------------------------------------------------------------
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
$dockerVersion = $null
$composeVersion = $null

if ($null -eq $dockerCmd) {
    Add-Result -Item "Docker CLI" -Actual "not found" -Required "Docker >= 24.0.0" -Status "FAIL"
}
else {
    $dockerVersionText = (& docker --version 2>$null | Out-String).Trim()
    $dockerVersion = Get-NumericVersion -Text $dockerVersionText
    Add-Result -Item "Docker CLI" -Actual $dockerVersionText -Required "Docker >= 24.0.0" `
        -Status $(if ($null -ne $dockerVersion -and $dockerVersion -ge [version]"24.0.0") { "PASS" } else { "FAIL" })

    $composeText = (& docker compose version 2>$null | Out-String).Trim()
    $composeVersion = Get-NumericVersion -Text $composeText
    Add-Result -Item "Docker Compose" -Actual $composeText -Required ">= v2.26.1" `
        -Status $(if ($null -ne $composeVersion -and $composeVersion -ge [version]"2.26.1") { "PASS" } else { "FAIL" })
}

$daemonUp = $false
$dockerInfo = $null
if ($null -ne $dockerCmd) {
    $rawInfo = (& docker info --format '{{json .}}' 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $rawInfo) {
        try {
            $dockerInfo = $rawInfo | ConvertFrom-Json
            $daemonUp = $true
        }
        catch {
            $daemonUp = $false
        }
    }
}

Add-Result -Item "Docker engine" -Actual $(if ($daemonUp) { "running, " + $dockerInfo.ServerVersion } else { "not reachable" }) `
    -Required ">= 24.0.0 and running" `
    -Status $(if ($daemonUp) { "PASS" } else { "FAIL" }) `
    -Note $(if (-not $daemonUp) { "Start Docker Desktop and wait for the engine before deploying." } else { "" })

$desktopExe = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
if (Test-Path -LiteralPath $desktopExe) {
    $desktopVersion = (Get-Item -LiteralPath $desktopExe).VersionInfo.ProductVersion
    Add-Result -Item "Docker Desktop" -Actual $desktopVersion -Required "info only" -Status "INFO"
}
else {
    Add-Result -Item "Docker Desktop" -Actual "not installed" -Required "Docker Desktop 4.x" -Status "WARN"
}

if ($daemonUp) {
    $vmCpu = $dockerInfo.NCPU
    $vmMemGb = [math]::Round([double]$dockerInfo.MemTotal / 1GB, 2)
    Add-Result -Item "Docker VM resources" -Actual ("{0} CPUs / {1} GB RAM / {2}" -f $vmCpu, $vmMemGb, $dockerInfo.Driver) `
        -Required ">= 4 CPUs / >= 12 GB RAM for a demo" `
        -Status $(if ($vmCpu -ge 4 -and $vmMemGb -ge 12) { "PASS" } elseif ($vmCpu -ge 4 -and $vmMemGb -ge 8) { "WARN" } else { "FAIL" }) `
        -Note $(if ($vmMemGb -lt 12) { "Raise memory in Docker Desktop or .wslconfig; Elasticsearch is the main consumer." } else { "" })

    $mapCount = $null
    $mapRaw = (& wsl -d docker-desktop sysctl -n vm.max_map_count 2>$null | Out-String)
    if (($mapRaw -replace '\s', '') -match '^(\d+)$') {
        $mapCount = [int]$Matches[1]
        Add-Result -Item "vm.max_map_count" -Actual ("{0}" -f $mapCount) `
            -Required ">= 262144" `
            -Status $(if ($mapCount -ge 262144) { "PASS" } else { "FAIL" }) `
            -Note $(if ($mapCount -lt 262144) { "Run: wsl -d docker-desktop sysctl -w vm.max_map_count=262144" } else { "" })
    }
    else {
        Add-Result -Item "vm.max_map_count" -Actual "unavailable" -Required ">= 262144" -Status "WARN" `
            -Note "Check inside the docker-desktop WSL distribution before starting Elasticsearch."
    }
}

$port = 8080
$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
Add-Result -Item "TCP port 8080" -Actual $(if ($listener) { "in use by PID " + (($listener | Select-Object -First 1).OwningProcess) } else { "free" }) `
    -Required "free for RAGFlow Web UI" `
    -Status $(if ($listener) { "WARN" } else { "PASS" }) `
    -Note $(if ($listener) { "Change SVR_WEB_HTTP_PORT in docs/ragflow/.env.example if needed." } else { "" })

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
Write-Output "# RAGFlow environment check"
Write-Output ""
Write-Output ("Generated: {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"))
Write-Output ""
Write-Output "| Item | Actual | Required | Result | Note |"
Write-Output "| --- | --- | --- | --- | --- |"
foreach ($r in $script:results) {
    Write-Output ("| {0} | {1} | {2} | **{3}** | {4} |" -f $r.Item, $r.Actual, $r.Required, $r.Status, $r.Note)
}

$failures = @($script:results | Where-Object { $_.Status -eq "FAIL" }).Count
$warnings = @($script:results | Where-Object { $_.Status -eq "WARN" }).Count

Write-Output ""
Write-Output "Summary: $($script:results.Count) checks, $failures FAIL, $warnings WARN."
Write-Output ""
if (-not $daemonUp) {
    Write-Output "Docker engine is not reachable. Start Docker Desktop, then run this script again."
}
elseif ($failures -gt 0) {
    Write-Output "Blocking issues found. Fix FAIL items before running docker compose."
}
elseif ($warnings -gt 0) {
    Write-Output "Docker is ready, but review WARN items before importing documents."
}
else {
    Write-Output "All checks passed. Proceed to docs/deployment.md."
}

if ($Strict -and ($failures -gt 0 -or $warnings -gt 0 -or -not $daemonUp)) {
    exit 1
}
exit 0
