Exit code: 0
Wall time: 0.5 seconds
Output:
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "Estate-Service-Config.ps1")

function Get-EstateService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ServiceId
    )

    $config = Get-EstateServiceConfig

    if (-not $config.Services.ContainsKey($ServiceId)) {
        throw "Unknown Estate service: $ServiceId"
    }

    return $config.Services[$ServiceId]
}

function Test-EstateHttpEndpoint {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Url,

        [int]$TimeoutSeconds = 4
    )

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -Method Get `
            -UseBasicParsing `
            -TimeoutSec $TimeoutSeconds `
            -ErrorAction Stop

        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    }
    catch {
        return $false
    }
}

function Test-EstateTcpPort {
    [CmdletBinding()]
    param(
        [string]$HostName = "127.0.0.1",

        [Parameter(Mandatory)]
        [int]$Port,

        [int]$TimeoutMilliseconds = 800
    )

    $client = New-Object System.Net.Sockets.TcpClient

    try {
        $result = $client.BeginConnect(
            $HostName,
            $Port,
            $null,
            $null
        )

        if (-not $result.AsyncWaitHandle.WaitOne($TimeoutMilliseconds)) {
            return $false
        }

        $client.EndConnect($result)
        return $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
        $client.Dispose()
    }
}

function Get-EstatePortOwners {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [int[]]$Ports
    )

    $results = @()

    foreach ($port in $Ports) {
        $connections = @(
            Get-NetTCPConnection `
                -State Listen `
                -LocalPort $port `
                -ErrorAction SilentlyContinue
        )

        foreach ($connection in $connections) {
            $processId = [int]$connection.OwningProcess

            $process = Get-CimInstance `
                -ClassName Win32_Process `
                -Filter "ProcessId = $processId" `
                -ErrorAction SilentlyContinue

            if ($null -eq $process) {
                continue
            }

            $results += [pscustomobject]@{
                port        = $port
                pid         = $processId
                name        = $process.Name
                executable  = $process.ExecutablePath
                commandLine = $process.CommandLine
                parentPid   = $process.ParentProcessId
            }
        }
    }

    return @($results | Sort-Object pid, port -Unique)
}

function Test-EstateProcessOwnership {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Process,

        [Parameter(Mandatory)]
        $Service
    )

    $pathText = @(
        [string]$Process.executable
        [string]$Process.name
        [string]$Process.commandLine
    ) -join " "

    $commandText = [string]$Process.commandLine

    $pathMatch = $false

    foreach ($fragment in @($Service.ExpectedPathFragments)) {
        if (
            -not [string]::IsNullOrWhiteSpace([string]$fragment) -and
            $pathText.IndexOf(
                [string]$fragment,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -ge 0
        ) {
            $pathMatch = $true
            break
        }
    }

    if (-not $pathMatch) {
        return $false
    }

    # Stream Deck can launch PowerShell in a context where Win32_Process
    # returns PID and executable but omits CommandLine.
    #
    # When that happens, a process listening on one of the service's
    # explicitly assigned ports may be accepted based on:
    #   1. expected executable/path match, and
    #   2. expected service port match.
    if ([string]::IsNullOrWhiteSpace($commandText)) {
        $processPort = 0

        if ($null -ne $Process.PSObject.Properties["port"]) {
            [void][int]::TryParse(
                [string]$Process.port,
                [ref]$processPort
            )
        }

        if ($processPort -gt 0 -and @($Service.Ports) -contains $processPort) {
            return $true
        }

        return $false
    }

    # Existing configuration uses a list of alternative identifying
    # fragments. A specific service fragment must be present.
    foreach ($fragment in @($Service.ExpectedCommandFragments)) {
        if (
            -not [string]::IsNullOrWhiteSpace([string]$fragment) -and
            $commandText.IndexOf(
                [string]$fragment,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -ge 0
        ) {
            return $true
        }
    }

    return $false
}

function Get-EstateMatchingProcesses {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Service
    )

    $results = @()

    $processes = Get-CimInstance `
        -ClassName Win32_Process `
        -ErrorAction SilentlyContinue

    foreach ($process in $processes) {
        $record = [pscustomobject]@{
            port        = $null
            pid         = [int]$process.ProcessId
            name        = $process.Name
            executable  = $process.ExecutablePath
            commandLine = $process.CommandLine
            parentPid   = [int]$process.ParentProcessId
        }

        if (Test-EstateProcessOwnership -Process $record -Service $Service) {
            $results += $record
        }
    }

    return @($results | Sort-Object pid -Unique)
}

function Get-EstateServiceRuntimeStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Service
    )

    $healthyUrl = $null

    foreach ($url in @($Service.HealthUrls)) {
        if (Test-EstateHttpEndpoint -Url $url) {
            $healthyUrl = $url
            break
        }
    }

    $portOwners = @(
        Get-EstatePortOwners -Ports @($Service.Ports)
    )

    $ownedPortProcesses = @(
        $portOwners |
            Where-Object {
                Test-EstateProcessOwnership `
                    -Process $_ `
                    -Service $Service
            }
    )

    $foreignPortProcesses = @(
        $portOwners |
            Where-Object {
                -not (
                    Test-EstateProcessOwnership `
                        -Process $_ `
                        -Service $Service
                )
            }
    )

    $matchingProcesses = @(
        Get-EstateMatchingProcesses -Service $Service
    )

    $configuredCommand = [string]$Service.Command
    $launchProcessMatches = @(
        $matchingProcesses |
            Where-Object {
                -not [string]::IsNullOrWhiteSpace([string]$_.executable) -and
                [string]::Equals(
                    [string]$_.executable,
                    $configuredCommand,
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            }
    )
    $duplicateLaunchProcesses = @(
        $launchProcessMatches | Sort-Object pid -Unique
    )

    $identityContract = (
        @($Service.ExpectedPathFragments).Count -gt 0 -or
        @($Service.ExpectedCommandFragments).Count -gt 0
    )
    $identityHealthy = (
        -not $identityContract -or
        (
            $ownedPortProcesses.Count -eq 1 -and
            $foreignPortProcesses.Count -eq 0 -and
            $duplicateLaunchProcesses.Count -le 1
        )
    )
    $healthy = ($null -ne $healthyUrl) -and $identityHealthy
    $state = if ($healthy) {
        "READY"
    }
    elseif ($foreignPortProcesses.Count -gt 0) {
        "PORT_OCCUPIED"
    }
    elseif ($identityContract -and ($ownedPortProcesses.Count -gt 1 -or $duplicateLaunchProcesses.Count -gt 1)) {
        "DUPLICATE"
    }
    elseif ($null -ne $healthyUrl -and $identityContract) {
        "IDENTITY_UNVERIFIED"
    }
    elseif ($portOwners.Count -gt 0) {
        "PORT_OCCUPIED"
    }
    elseif ($matchingProcesses.Count -gt 0) {
        "STALE"
    }
    else {
        "OFF"
    }

    return [pscustomobject]@{
        id                    = $Service.Id
        name                  = $Service.Name
        core                  = [bool]$Service.Core
        healthy               = $healthy
        state                 = $state
        healthyUrl            = $healthyUrl
        ports                 = @($Service.Ports)
        portOwners            = $portOwners
        ownedPortProcesses    = $ownedPortProcesses
        foreignPortProcesses  = $foreignPortProcesses
        matchingProcesses     = $matchingProcesses
        identityContract      = $identityContract
        identityHealthy       = $identityHealthy
        duplicateLaunchProcesses = $duplicateLaunchProcesses
    }
}

function Wait-EstateServiceState {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Service,

        [Parameter(Mandatory)]
        [bool]$Healthy,

        [int]$TimeoutSeconds = 90,

        [int]$PollSeconds = 2
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        $status = Get-EstateServiceRuntimeStatus -Service $Service

        if ([bool]$status.healthy -eq $Healthy) {
            return $status
        }

        Start-Sleep -Seconds $PollSeconds
    }
    while ((Get-Date) -lt $deadline)

    return Get-EstateServiceRuntimeStatus -Service $Service
}

function Resolve-EstateCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Command
    )

    if (Test-Path -LiteralPath $Command -PathType Leaf) {
        return (Resolve-Path -LiteralPath $Command).Path
    }

    $resolved = Get-Command $Command -ErrorAction SilentlyContinue

    if ($null -eq $resolved) {
        throw "Command not found: $Command"
    }

    return $resolved.Source
}

function Stop-EstateServiceProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Service,

        [switch]$AllOwnedInstances
    )

    $status = Get-EstateServiceRuntimeStatus -Service $Service

    if ($status.foreignPortProcesses.Count -gt 0) {
        $foreignDescription = @(
            $status.foreignPortProcesses |
                ForEach-Object {
                    "Port $($_.port), PID $($_.pid), $($_.name), $($_.commandLine)"
                }
        ) -join "; "

        throw "Refusing to stop $($Service.Name). A foreign process owns an expected port: $foreignDescription"
    }

    $targets = @()

    if ($AllOwnedInstances) {
        $targets = @(
            @($status.matchingProcesses) +
            @($status.ownedPortProcesses)
        )
    }
    else {
        $targets = @($status.ownedPortProcesses)
    }

    $targets = @(
        $targets |
            Where-Object { $null -ne $_.pid } |
            Sort-Object pid -Unique
    )

    if ($targets.Count -eq 0) {
        return [pscustomobject]@{
            id      = $Service.Id
            name    = $Service.Name
            action  = "stop"
            result  = "already_stopped"
            state   = "OFF"
            stopped = @()
            exited  = @()
        }
    }

    $stopped = @()
    $alreadyExited = @()

    # Child and listener processes can disappear automatically after another
    # member of the same service process tree is stopped. That is successful
    # shutdown behavior, not an error.
    foreach ($target in $targets) {
        $targetId = [int]$target.pid

        $liveProcess = Get-Process `
            -Id $targetId `
            -ErrorAction SilentlyContinue

        if ($null -eq $liveProcess) {
            $alreadyExited += [pscustomobject]@{
                pid         = $targetId
                name        = $target.name
                executable  = $target.executable
                commandLine = $target.commandLine
                result      = "already_exited"
            }

            continue
        }

        try {
            Stop-Process `
                -Id $targetId `
                -Force `
                -ErrorAction Stop

            $stopped += [pscustomobject]@{
                pid         = $targetId
                name        = $target.name
                executable  = $target.executable
                commandLine = $target.commandLine
                result      = "stopped"
            }
        }
        catch {
            # Recheck because another stopped process may have caused this
            # process to exit between Get-Process and Stop-Process.
            $stillExists = Get-Process `
                -Id $targetId `
                -ErrorAction SilentlyContinue

            if ($null -eq $stillExists) {
                $alreadyExited += [pscustomobject]@{
                    pid         = $targetId
                    name        = $target.name
                    executable  = $target.executable
                    commandLine = $target.commandLine
                    result      = "exited_during_shutdown"
                }

                continue
            }

            throw "Failed to stop $($Service.Name) PID ${targetId}: $($_.Exception.Message)"
        }
    }

    $finalStatus = Wait-EstateServiceState `
        -Service $Service `
        -Healthy $false `
        -TimeoutSeconds 30 `
        -PollSeconds 1

    if ($finalStatus.healthy) {
        throw "$($Service.Name) still responds after its owned processes were stopped."
    }

    return [pscustomobject]@{
        id      = $Service.Id
        name    = $Service.Name
        action  = "stop"
        result  = "stopped"
        state   = "OFF"
        stopped = $stopped
        exited  = $alreadyExited
    }
}

function Start-EstateServiceProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        $Service
    )

    $startMutex = [System.Threading.Mutex]::new($false, "Estate.Service.Start.$($Service.Id)")
    $lockHeld = $false
    try {
        try {
            $lockHeld = $startMutex.WaitOne(120000)
        }
        catch [System.Threading.AbandonedMutexException] {
            $lockHeld = $true
        }
        if (-not $lockHeld) {
            throw "Timed out waiting for the governed $($Service.Name) start lock."
        }

        $initialStatus = Get-EstateServiceRuntimeStatus -Service $Service

    if ($initialStatus.healthy) {
        return [pscustomobject]@{
            id     = $Service.Id
            name   = $Service.Name
            action = "start"
            result = "already_running"
            state  = "READY"
            pid    = $null
            health = $initialStatus
        }
    }

    if ($initialStatus.foreignPortProcesses.Count -gt 0) {
        $foreignDescription = @(
            $initialStatus.foreignPortProcesses |
                ForEach-Object {
                    "Port $($_.port), PID $($_.pid), $($_.name), $($_.commandLine)"
                }
        ) -join "; "

        throw "Cannot start $($Service.Name). An expected port is owned by a foreign process: $foreignDescription"
    }

    if (
        $initialStatus.ownedPortProcesses.Count -gt 0 -or
        $initialStatus.matchingProcesses.Count -gt 0
    ) {
        [void](
            Stop-EstateServiceProcess `
                -Service $Service `
                -AllOwnedInstances
        )
    }

    $command = Resolve-EstateCommand -Command $Service.Command

    $workingDirectory = if (
        $Service.ContainsKey("WorkingDirectory") -and
        -not [string]::IsNullOrWhiteSpace(
            [string]$Service.WorkingDirectory
        )
    ) {
        [string]$Service.WorkingDirectory
    }
    else {
        Split-Path -Parent $command
    }

    if (-not (Test-Path -LiteralPath $workingDirectory -PathType Container)) {
        throw "Working directory not found for $($Service.Name): $workingDirectory"
    }

    $stateRoot = (Get-EstateServiceConfig).StateRoot
    $logRoot = Join-Path $stateRoot "logs"

    New-Item `
        -ItemType Directory `
        -Path $logRoot `
        -Force |
        Out-Null

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stdoutPath = Join-Path $logRoot "$($Service.Id)-$timestamp.stdout.log"
    $stderrPath = Join-Path $logRoot "$($Service.Id)-$timestamp.stderr.log"

    $environmentBackup = @{}

    try {
        if ($Service.ContainsKey("Environment")) {
            foreach ($entry in $Service.Environment.GetEnumerator()) {
                $environmentBackup[$entry.Key] = [Environment]::GetEnvironmentVariable(
                    $entry.Key,
                    "Process"
                )

                [Environment]::SetEnvironmentVariable(
                    $entry.Key,
                    [string]$entry.Value,
                    "Process"
                )
            }
        }

        if (
            [System.IO.Path]::GetExtension($command) -ieq ".bat" -or
            [System.IO.Path]::GetExtension($command) -ieq ".cmd"
        ) {
            $argumentList = @(
                "/d",
                "/c",
                "`"$command`""
            ) + @($Service.Arguments)

            $process = Start-Process `
                -FilePath "$env:SystemRoot\System32\cmd.exe" `
                -ArgumentList $argumentList `
                -WorkingDirectory $workingDirectory `
                -RedirectStandardOutput $stdoutPath `
                -RedirectStandardError $stderrPath `
                -WindowStyle Hidden `
                -PassThru
        }
        else {
            $process = Start-Process `
                -FilePath $command `
                -ArgumentList @($Service.Arguments) `
                -WorkingDirectory $workingDirectory `
                -RedirectStandardOutput $stdoutPath `
                -RedirectStandardError $stderrPath `
                -WindowStyle Hidden `
                -PassThru
        }
    }
    finally {
        foreach ($entry in $environmentBackup.GetEnumerator()) {
            [Environment]::SetEnvironmentVariable(
                $entry.Key,
                $entry.Value,
                "Process"
            )
        }
    }

    $finalStatus = Wait-EstateServiceState `
        -Service $Service `
        -Healthy $true `
        -TimeoutSeconds 120 `
        -PollSeconds 2

    if (-not $finalStatus.healthy) {
        throw "$($Service.Name) was launched but did not become healthy. Review $stdoutPath and $stderrPath"
    }

        return [pscustomobject]@{
            id       = $Service.Id
            name     = $Service.Name
            action   = "start"
            result   = "started"
            state    = "READY"
            pid      = $process.Id
            stdout   = $stdoutPath
            stderr   = $stderrPath
            health   = $finalStatus
        }
    }
    finally {
        if ($lockHeld) {
            try { $startMutex.ReleaseMutex() } catch { }
        }
        $startMutex.Dispose()
    }
}

function Get-EstateRepositoryCommit {
    [CmdletBinding()]
    param()

    $config = Get-EstateServiceConfig

    try {
        $commit = & git `
            -C $config.EstateRoot `
            rev-parse `
            --short=12 `
            HEAD 2>$null

        return ([string]$commit).Trim()
    }
    catch {
        return $null
    }
}

function Get-EstateCoreHealthData {
    [CmdletBinding()]
    param()

    $coreIds = @(
        "ollama",
        "resident_gateway",
        "open_webui"
    )

    $services = @()

    foreach ($serviceId in $coreIds) {
        $service = Get-EstateService -ServiceId $serviceId
        $services += Get-EstateServiceRuntimeStatus -Service $service
    }

    $readyCount = @(
        $services |
            Where-Object { $_.healthy }
    ).Count

    return [pscustomobject]@{
        label    = "CORE $readyCount/3"
        ready    = ($readyCount -eq 3)
        count    = $readyCount
        total    = 3
        commit   = Get-EstateRepositoryCommit
        services = $services
    }
}

function Start-EstateCore {
    [CmdletBinding()]
    param(
        [switch]$OpenBrowser
    )

    $results = @()

    foreach ($serviceId in @(
        "ollama",
        "resident_gateway",
        "open_webui"
    )) {
        $service = Get-EstateService -ServiceId $serviceId

        $results += Start-EstateServiceProcess -Service $service
    }

    if ($OpenBrowser) {
        Start-Process "http://127.0.0.1:8080/"
    }

    return [pscustomobject]@{
        action  = "start_core"
        result  = "complete"
        health  = Get-EstateCoreHealthData
        services = $results
    }
}

function Stop-EstateCore {
    [CmdletBinding()]
    param(
        [switch]$IncludeProvider
    )

    # IncludeProvider is retained for wrapper compatibility.
    # Approved Core semantics always stop all three Core services.
    $results = @()

    foreach ($serviceId in @(
        "open_webui",
        "resident_gateway",
        "ollama"
    )) {
        $service = Get-EstateService -ServiceId $serviceId

        $results += Stop-EstateServiceProcess `
            -Service $service `
            -AllOwnedInstances
    }

    return [pscustomobject]@{
        action   = "stop_core"
        result   = "complete"
        health   = Get-EstateCoreHealthData
        services = $results
    }
}

function Restart-EstateCore {
    [CmdletBinding()]
    param(
        [switch]$IncludeProvider
    )

    $stopResult = Stop-EstateCore -IncludeProvider
    Start-Sleep -Seconds 2
    $startResult = Start-EstateCore

    return [pscustomobject]@{
        action = "restart_core"
        result = "complete"
        stop   = $stopResult
        start  = $startResult
        health = Get-EstateCoreHealthData
    }
}




