[CmdletBinding()]
param(
    [switch]$Json,
    [string]$NvidiaSmiOutput,
    [string]$ComputeAppsOutput,
    [string]$PnpOutput,
    [string]$ProcessFixture,
    [string]$PortFixture,
    [string]$RepoRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$UseNvidiaSmiFixture = $PSBoundParameters.ContainsKey('NvidiaSmiOutput')
$UseComputeAppsFixture = $PSBoundParameters.ContainsKey('ComputeAppsOutput')
$UsePnpFixture = $PSBoundParameters.ContainsKey('PnpOutput')
$UseProcessFixture = $PSBoundParameters.ContainsKey('ProcessFixture')
$UsePortFixture = $PSBoundParameters.ContainsKey('PortFixture')

# Conservative, named policy values.  VRAM residency alone is not material;
# active utilization/power is the signal that blocks a new bounded acceptance.
$MaterialUtilizationPercent = 20
$MaterialPowerWatts = 75
$MaterialProcessMemoryMiB = 1024
$ExitPass = 0
$ExitBlocked = 2
$ExitHealthFailure = 3
$ExitToolError = 4

$ExpectedResources = @(
    [ordered]@{
        resource_id = 'DESKTOP-JA3RPNQ:nvidia:GPU-46f3fd00-5454-4536-4196-5d8b727e14f2'
        gpu_uuid = 'GPU-46f3fd00-5454-4536-4196-5d8b727e14f2'
        expected_name = 'NVIDIA GeForce RTX 4090'
        pci_bus = '00000000:07:00.0'
        lane_id = 'qwen.local.text.4090'
        lane_port = 12409
        minimum_safe_free_mib = 8192
    },
    [ordered]@{
        resource_id = 'DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414'
        gpu_uuid = 'GPU-6785b322-899d-8eec-e817-31d83279a414'
        expected_name = 'Tesla P100-PCIE-16GB'
        pci_bus = '00000000:04:00.0'
        lane_id = 'qwen.local.text.p100-1'
        lane_port = 12100
        minimum_safe_free_mib = 4096
    }
)

function Convert-ToNumber([object]$Value) {
    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value) -or [string]$Value -eq '[N/A]') { return $null }
    $number = 0.0
    if ([double]::TryParse(([string]$Value).Trim(), [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) { return $number }
    return $null
}

function Get-Field([object]$Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Read-JsonFixture([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-CommandOutput([string]$Command, [string[]]$Arguments) {
    $output = & $Command @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$Command failed with exit code $LASTEXITCODE" }
    return (($output | ForEach-Object { [string]$_ }) -join "`n")
}

function Get-NvidiaRows([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { throw 'nvidia-smi returned no GPU rows' }
    foreach ($line in @($Raw.Trim() -split "`r?`n")) {
        if (@($line -split ',').Count -ne 9) { throw 'nvidia-smi returned malformed GPU telemetry columns' }
    }
    $header = @('uuid','name','pci_bus','memory_used_mib','memory_free_mib','memory_total_mib','utilization_percent','temperature_c','power_w')
    $rows = ConvertFrom-Csv -Header $header -InputObject ($Raw.Trim())
    if (@($rows).Count -lt 1) { throw 'nvidia-smi returned no parseable GPU rows' }
    return @($rows)
}

function Get-ComputeRows([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { return @() }
    $header = @('pid','process_name','used_memory_mib','gpu_uuid')
    return @(ConvertFrom-Csv -Header $header -InputObject ($Raw.Trim()))
}

function Get-ProcessMap([object]$Fixture, [bool]$UseFixture) {
    $map = @{}
    if ($UseFixture) {
        foreach ($item in @($Fixture)) { $pidValue = Get-Field $item 'pid'; if ($null -ne $pidValue) { $map[[string]$pidValue] = $item } }
        return $map
    }
    foreach ($process in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $map[[string]$process.ProcessId] = [ordered]@{
            pid = [int]$process.ProcessId
            name = $process.Name
            executable_path = $process.ExecutablePath
            command_line = $process.CommandLine
            parent_pid = $process.ParentProcessId
        }
    }
    return $map
}

function Get-PortMap([object]$Fixture, [bool]$UseFixture) {
    $map = @{}
    if ($UseFixture) {
        foreach ($item in @($Fixture)) { $portValue = Get-Field $item 'port'; if ($null -ne $portValue) { $map[[string]$portValue] = $item } }
        return $map
    }
    foreach ($connection in @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue)) {
        $key = [string]$connection.LocalPort
        if (-not $map.ContainsKey($key)) {
            $map[$key] = [ordered]@{ port = [int]$connection.LocalPort; pid = [int]$connection.OwningProcess }
        }
    }
    return $map
}

function Test-EstateOwnership([object]$Process, [int]$Port, [string]$Root, [string]$LaneId) {
    if ($null -eq $Process) { return 'UNKNOWN' }
    $evidence = @([string]$Process.executable_path, [string]$Process.command_line) -join ' '
    if ($evidence -match [regex]::Escape($Root) -or $evidence -match [regex]::Escape($LaneId)) { return 'ESTATE_OWNED' }
    $evidencePath = Join-Path $Root 'runtime/compute_resources/runtime_lanes.json'
    if (Test-Path -LiteralPath $evidencePath) {
        try {
            $payload = Get-Content -LiteralPath $evidencePath -Raw | ConvertFrom-Json
            foreach ($lane in @($payload.lanes)) {
                if ([int]$lane.process_id -eq [int]$Process.pid -and [string]$lane.runtime_lane_id -eq $LaneId) { return 'ESTATE_OWNED' }
            }
        } catch { }
    }
    if ($evidence -match 'Ollama|llama-server|ollama.exe|dwm.exe|explorer.exe|chrome.exe|msedge') { return 'EXTERNAL' }
    return 'UNKNOWN'
}

function Get-ProcessRecord([object]$Row, [hashtable]$ProcessMap, [int]$Port, [string]$Root, [string]$LaneId) {
    $pidValue = Convert-ToNumber (Get-Field $Row 'pid')
    $process = if ($null -ne $pidValue) { $ProcessMap[[string][int]$pidValue] } else { $null }
    $ownership = Test-EstateOwnership $process $Port $Root $LaneId
    return [ordered]@{
        pid = if ($null -ne $pidValue) { [int]$pidValue } else { $null }
        process_name = [string]$Row.process_name
        used_memory_mib = Convert-ToNumber $Row.used_memory_mib
        gpu_uuid = [string]$Row.gpu_uuid
        executable_path = if ($null -ne $process) { $process.executable_path } else { $null }
        command_line = if ($null -ne $process) { $process.command_line } else { $null }
        parent_pid = if ($null -ne $process) { $process.parent_pid } else { $null }
        ownership = $ownership
    }
}

function Get-PortRecord([hashtable]$PortMap, [hashtable]$ProcessMap, [int]$Port, [string]$Root, [string]$LaneId) {
    $row = $PortMap[[string]$Port]
    if ($null -eq $row) { return [ordered]@{ listening = $false; port = $Port; pid = $null; process_name = $null; ownership = $null } }
    $process = $ProcessMap[[string][int](Get-Field $row 'pid')]
    $ownership = Test-EstateOwnership $process $Port $Root $LaneId
    return [ordered]@{
        listening = $true
        port = $Port
        pid = [int](Get-Field $row 'pid')
        process_name = if ($null -ne $process) { $process.name } else { $null }
        executable_path = if ($null -ne $process) { $process.executable_path } else { $null }
        command_line = if ($null -ne $process) { $process.command_line } else { $null }
        ownership = $ownership
    }
}

function Get-PnpMap([object]$Fixture) {
    $map = @{}
    if ($null -ne $Fixture) {
        foreach ($item in @($Fixture)) { $map[[string]$item.name] = $item }
        return $map
    }
    foreach ($device in @(Get-PnpDevice -Class Display -ErrorAction SilentlyContinue)) {
        $map[[string]$device.FriendlyName] = [ordered]@{ name = $device.FriendlyName; status = $device.Status; problem_code = $device.ProblemCode }
    }
    return $map
}

function Invoke-Preflight {
    try {
        $smi = if ($UseNvidiaSmiFixture) { $NvidiaSmiOutput } else { Get-CommandOutput 'nvidia-smi' @('--query-gpu=uuid,name,pci.bus_id,memory.used,memory.free,memory.total,utilization.gpu,temperature.gpu,power.draw','--format=csv,noheader,nounits') }
        $apps = if ($UseComputeAppsFixture) { $ComputeAppsOutput } else { Get-CommandOutput 'nvidia-smi' @('--query-compute-apps=pid,process_name,used_memory,gpu_uuid','--format=csv,noheader,nounits') }
        $gpuRows = Get-NvidiaRows $smi
        $computeRows = Get-ComputeRows $apps
        $pnp = Get-PnpMap (Read-JsonFixture $PnpOutput)
        $processes = Get-ProcessMap (Read-JsonFixture $ProcessFixture) $UseProcessFixture
        $ports = Get-PortMap (Read-JsonFixture $PortFixture) $UsePortFixture
        $resources = @()
        $globalReasons = @()
        foreach ($expected in $ExpectedResources) {
            $row = @($gpuRows | Where-Object { $_.uuid -eq $expected.gpu_uuid }) | Select-Object -First 1
            $reasons = @()
            $health = 'OK'
            if ($null -eq $row) {
                $health = 'FAILURE'; $reasons += "expected GPU UUID is missing: $($expected.gpu_uuid)"
            }
            $pnpRow = $pnp[$expected.expected_name]
            if ($null -eq $pnpRow -or [string]$pnpRow.status -ne 'OK') {
                $health = 'FAILURE'; $reasons += "PnP status is not OK for $($expected.expected_name)"
            }
            if ($null -ne $row -and $row.pci_bus -ne $expected.pci_bus) { $health = 'FAILURE'; $reasons += "PCI identity mismatch: expected $($expected.pci_bus), observed $($row.pci_bus)" }
            if ($null -ne $row -and [string]$row.name -ne $expected.expected_name) { $health = 'FAILURE'; $reasons += "GPU name mismatch: expected $($expected.expected_name), observed $($row.name)" }
            $memoryFree = if ($null -ne $row) { Convert-ToNumber $row.memory_free_mib } else { $null }
            $memoryUsed = if ($null -ne $row) { Convert-ToNumber $row.memory_used_mib } else { $null }
            $memoryTotal = if ($null -ne $row) { Convert-ToNumber $row.memory_total_mib } else { $null }
            $util = if ($null -ne $row) { Convert-ToNumber $row.utilization_percent } else { $null }
            $temp = if ($null -ne $row) { Convert-ToNumber $row.temperature_c } else { $null }
            $power = if ($null -ne $row) { Convert-ToNumber $row.power_w } else { $null }
            if ($null -ne $row -and ($null -eq $memoryFree -or $null -eq $memoryTotal -or $null -eq $util)) { $health = 'FAILURE'; $reasons += 'nvidia-smi returned incomplete device telemetry' }
            if ($null -ne $memoryFree -and $memoryFree -lt $expected.minimum_safe_free_mib) { $reasons += "free VRAM $memoryFree MiB is below the accepted floor $($expected.minimum_safe_free_mib) MiB" }
            $gpuProcesses = @($computeRows | Where-Object { $_.gpu_uuid -eq $expected.gpu_uuid } | ForEach-Object { Get-ProcessRecord $_ $processes $expected.lane_port $RepoRoot $expected.lane_id })
            $material = $false
            $unknownComputeOwnership = $false
            foreach ($proc in $gpuProcesses) {
                if ($proc.ownership -eq 'UNKNOWN') {
                    $unknownComputeOwnership = $true
                } elseif ($proc.ownership -ne 'ESTATE_OWNED' -and (($null -ne $util -and $util -ge $MaterialUtilizationPercent) -or ($null -ne $power -and $power -ge $MaterialPowerWatts) -or ($null -ne $proc.used_memory_mib -and $proc.used_memory_mib -ge $MaterialProcessMemoryMiB -and $null -ne $util -and $util -ge 10))) { $material = $true }
            }
            if ($material) { $reasons += "material external compute activity: utilization/power/process memory crossed named preflight thresholds" }
            if ($unknownComputeOwnership) { $reasons += 'compute process ownership is UNKNOWN; conservative preflight blocks the lane' }
            $port = Get-PortRecord $ports $processes $expected.lane_port $RepoRoot $expected.lane_id
            if ($port.listening -and $port.ownership -ne 'ESTATE_OWNED') { $reasons += "lane port $($expected.lane_port) is occupied by $($port.ownership) PID $($port.pid)" }
            $ready = ($health -eq 'OK' -and $null -ne $memoryFree -and $memoryFree -ge $expected.minimum_safe_free_mib -and -not $material -and -not $unknownComputeOwnership -and (-not $port.listening -or $port.ownership -eq 'ESTATE_OWNED'))
            if (-not $ready -and $health -eq 'OK' -and $reasons.Count -eq 0) { $reasons += 'lane is not ready under the conservative preflight policy' }
            $resources += [ordered]@{
                resource_id = $expected.resource_id; gpu_uuid = $expected.gpu_uuid; name = if ($null -ne $row) { [string]$row.name } else { $null }; pci_bus = if ($null -ne $row) { [string]$row.pci_bus } else { $null }; health = $health; pnp_status = if ($null -ne $pnpRow) { [string]$pnpRow.status } else { 'MISSING' }; nvml_visible = ($null -ne $row); memory_used_mib = $memoryUsed; memory_free_mib = $memoryFree; memory_total_mib = $memoryTotal; minimum_safe_free_mib = $expected.minimum_safe_free_mib; utilization_percent = $util; temperature_c = $temp; power_w = $power; lane_id = $expected.lane_id; lane_port = $expected.lane_port; lane_port_owner = $port; compute_processes = $gpuProcesses; material_external_load = $material; unknown_compute_ownership = $unknownComputeOwnership; ready = $ready; reasons = $reasons
            }
            if ($health -ne 'OK') { $globalReasons += $reasons }
            elseif (-not $ready) { $globalReasons += $reasons }
        }
        $status = if (@($resources | Where-Object { $_.health -ne 'OK' }).Count -gt 0) { 'GPU_HEALTH_FAILURE' } elseif ($globalReasons.Count -gt 0) { 'PRECHECK_BLOCKED' } else { 'PASS' }
        return [ordered]@{ status = $status; timestamp = (Get-Date).ToUniversalTime().ToString('o'); host = $env:COMPUTERNAME; resources = $resources; reasons = @($globalReasons | Select-Object -Unique); policy = [ordered]@{ material_utilization_percent = $MaterialUtilizationPercent; material_power_watts = $MaterialPowerWatts; material_process_memory_mib = $MaterialProcessMemoryMiB; note = 'VRAM residency alone is not material; active compute and conflicting lane ports block acceptance.' }; exit_code = switch ($status) { 'PASS' { $ExitPass } 'PRECHECK_BLOCKED' { $ExitBlocked } 'GPU_HEALTH_FAILURE' { $ExitHealthFailure } default { $ExitToolError } } }
    } catch {
        return [ordered]@{ status = 'PREFLIGHT_TOOL_ERROR'; timestamp = (Get-Date).ToUniversalTime().ToString('o'); host = $env:COMPUTERNAME; resources = @(); reasons = @([string]$_.Exception.Message); policy = $null; exit_code = $ExitToolError }
    }
}

$result = Invoke-Preflight
if ($Json) { $result | ConvertTo-Json -Depth 12 }
else {
    Write-Output 'EC-000223 DUAL-GPU PREFLIGHT'
    foreach ($resource in $result.resources) {
        Write-Output "`n$($resource.name)"
        Write-Output "  Health:      $($resource.health)"
        Write-Output "  UUID:        $($resource.gpu_uuid)"
        Write-Output "  PCI:         $($resource.pci_bus)"
        Write-Output "  VRAM:        $($resource.memory_used_mib) / $($resource.memory_total_mib) MiB"
        Write-Output "  Free:        $($resource.memory_free_mib) MiB"
        Write-Output "  Utilization: $($resource.utilization_percent) %"
        Write-Output "  Power:       $($resource.power_w) W"
        Write-Output "  Port $($resource.lane_port): $($resource.lane_port_owner.ownership) PID $($resource.lane_port_owner.pid)"
        Write-Output "  Lane ready:  $($resource.ready)"
        foreach ($reason in $resource.reasons) { Write-Output "  Reason:      $reason" }
    }
    Write-Output "`nRESULT: $($result.status)"
    foreach ($reason in $result.reasons) { Write-Output "- $reason" }
}
exit ([int]$result.exit_code)
