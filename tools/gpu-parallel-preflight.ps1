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
        pnp_vendor_device_id = 'VEN_10DE&DEV_2684'
        pnp_product_pattern = 'GeForce RTX 4090'
        prior_observed_pci_bus = '00000000:07:00.0'
        lane_id = 'qwen.local.text.4090'
        lane_port = 12409
        minimum_safe_free_mib = 8192
    },
    [ordered]@{
        resource_id = 'DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414'
        gpu_uuid = 'GPU-6785b322-899d-8eec-e817-31d83279a414'
        expected_name = 'Tesla P100-PCIE-16GB'
        pnp_vendor_device_id = 'VEN_10DE&DEV_15F8'
        pnp_product_pattern = 'Tesla P100'
        prior_observed_pci_bus = '00000000:04:00.0'
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
    if ($Object -is [System.Collections.IDictionary]) {
        foreach ($key in @($Object.Keys)) {
            if ([string]$key -ieq $Name) { return $Object[$key] }
        }
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Normalize-PidKey([object]$Value) {
    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) { return $null }
    $pidNumber = 0L
    if (-not [long]::TryParse(([string]$Value).Trim(), [Globalization.NumberStyles]::Integer, [Globalization.CultureInfo]::InvariantCulture, [ref]$pidNumber) -or $pidNumber -le 0) { return $null }
    return $pidNumber.ToString([Globalization.CultureInfo]::InvariantCulture)
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
        if (@($line -split ',').Count -ne 10) { throw 'nvidia-smi returned malformed GPU telemetry columns' }
    }
    $header = @('uuid','name','pci_bus','memory_used_mib','memory_free_mib','memory_total_mib','utilization_percent','temperature_c','power_w','driver_model')
    $rows = ConvertFrom-Csv -Header $header -InputObject ($Raw.Trim())
    if (@($rows).Count -lt 1) { throw 'nvidia-smi returned no parseable GPU rows' }
    return @($rows)
}

function Get-ComputeRows([string]$Raw) {
    if ([string]::IsNullOrWhiteSpace($Raw)) { return @() }
    $header = @('pid','process_name','used_memory_mib','gpu_uuid')
    return @(ConvertFrom-Csv -Header $header -InputObject ($Raw.Trim()))
}

function Get-GpuEngineTypeMap {
    $map = @{}
    $errorMessage = $null
    $sampleCount = 0
    try {
        $sample = Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction Stop
        $sampleCount = @($sample.CounterSamples).Count
        foreach ($counter in @($sample.CounterSamples)) {
            if ([string]$counter.InstanceName -match '^pid_(?<pid>\d+)_.*engtype_(?<engine>.+)$') {
                $pidKey = Normalize-PidKey $Matches.pid
                if ($null -eq $pidKey) { continue }
                $map[$pidKey] = @(@($map[$pidKey]) + [string]$Matches.engine | Select-Object -Unique)
            }
        }
    } catch { $errorMessage = [string]$_.Exception.Message }
    return [ordered]@{ map = $map; available = ($map.Count -gt 0); sample_count = $sampleCount; error = $errorMessage }
}

function Get-ProcessMap([object]$Fixture, [bool]$UseFixture) {
    $map = @{}
    if ($UseFixture) {
        foreach ($item in @($Fixture)) {
            $pidKey = Normalize-PidKey (Get-Field $item 'pid')
            if ($null -eq $pidKey) { continue }
            $record = [ordered]@{}
            foreach ($property in @($item.PSObject.Properties)) { $record[$property.Name] = $property.Value }
            $map[$pidKey] = $record
        }
        return [ordered]@{ processes = $map; gpu_engine_collection = [ordered]@{ available = $null; sample_count = $null; error = $null; source = 'fixture' } }
    }
    $gpuEngineCollection = Get-GpuEngineTypeMap
    $gpuEngineTypes = $gpuEngineCollection.map
    foreach ($process in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        $pidKey = Normalize-PidKey $process.ProcessId
        if ($null -eq $pidKey) { continue }
        $map[$pidKey] = [ordered]@{
            pid = [int]$process.ProcessId
            name = $process.Name
            executable_path = $process.ExecutablePath
            command_line = $process.CommandLine
            parent_pid = $process.ParentProcessId
            gpu_engine_types = @($gpuEngineTypes[$pidKey])
        }
    }
    return [ordered]@{ processes = $map; gpu_engine_collection = [ordered]@{ available = $gpuEngineCollection.available; sample_count = $gpuEngineCollection.sample_count; error = $gpuEngineCollection.error; source = 'windows_gpu_engine_performance_counter' } }
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
    $evidence = @([string](Get-Field $Process 'executable_path'), [string](Get-Field $Process 'command_line')) -join ' '
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
    return 'UNKNOWN'
}

function Test-ActiveExternalCompute([object]$Process, [object]$Row, [object[]]$EngineTypes, [object]$PortRecord) {
    $evidence = @([string](Get-Field $Process 'executable_path'), [string](Get-Field $Process 'command_line'), [string](Get-Field $Row 'process_name')) -join ' '
    $usedMemory = Convert-ToNumber (Get-Field $Row 'used_memory_mib')
    $hasComputeEngine = @($EngineTypes | Where-Object { [string]$_ -match '(?i)compute|cuda' }).Count -gt 0
    $foreignLanePort = $null -ne $PortRecord -and [bool]$PortRecord.listening -and [string]$PortRecord.ownership -ne 'ESTATE_OWNED'
    $modelWorkerSignature = $evidence -match '(?i)llama-server|vllm|text-generation|stable-diffusion|(?:^|\s)--model(?:[=\s])|\.gguf(?:\s|$)'
    return $foreignLanePort -or $hasComputeEngine -or $modelWorkerSignature
}

function Get-ProcessRecord([object]$Row, [hashtable]$ProcessMap, [int]$Port, [string]$Root, [string]$LaneId, [string]$DriverModel, [object]$Utilization, [object]$Power, [object]$PortRecord, [bool]$UseFixture) {
    $pidKey = Normalize-PidKey (Get-Field $Row 'pid')
    $process = if ($null -ne $pidKey) { $ProcessMap[$pidKey] } else { $null }
    $fixtureLookupState = if ($null -ne $process) { [string](Get-Field $process 'lookup_state') } else { $null }
    $processLookupState = if ($null -ne $process -and $fixtureLookupState -ne 'exited') { 'RESOLVED' } else { 'UNRESOLVED' }
    $ownership = if ($fixtureLookupState -eq 'exited') { 'TRANSIENT_EXITED' } else { Test-EstateOwnership $process $Port $Root $LaneId }
    if ($null -eq $process -and -not $UseFixture -and $null -ne $pidKey) {
        $activeProcess = Get-Process -Id ([int64]$pidKey) -ErrorAction SilentlyContinue
        if ($null -eq $activeProcess) { $processLookupState = 'EXITED_AFTER_NVIDIA_SNAPSHOT'; $ownership = 'TRANSIENT_EXITED' }
        else { $processLookupState = 'ACTIVE_UNRESOLVED'; $ownership = 'UNKNOWN' }
    } elseif ($fixtureLookupState -eq 'exited') {
        $processLookupState = 'EXITED_AFTER_NVIDIA_SNAPSHOT'
    }
    $usedMemory = Convert-ToNumber $Row.used_memory_mib
    $engineTypes = @()
    if ($null -ne $process) { $engineTypes = @((Get-Field $process 'gpu_engine_types') | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }) }
    $hasComputeEngine = @($engineTypes | Where-Object { [string]$_ -match '(?i)compute|cuda' }).Count -gt 0
    $hasCompleteProcessMetadata = $null -ne $process -and -not [string]::IsNullOrWhiteSpace([string](Get-Field $process 'executable_path')) -and -not [string]::IsNullOrWhiteSpace([string](Get-Field $process 'command_line'))
    $lowAggregateLoad = $null -ne $Utilization -and $null -ne $Power -and [double]$Utilization -lt $MaterialUtilizationPercent -and [double]$Power -lt $MaterialPowerWatts
    $lanePortSafe = $null -ne $PortRecord -and (-not [bool]$PortRecord.listening -or [string]$PortRecord.ownership -eq 'ESTATE_OWNED')
    $positiveGraphicsContext = @($engineTypes).Count -gt 0 -and -not $hasComputeEngine
    $boundedWddmFallback = @($engineTypes).Count -eq 0 -and $lowAggregateLoad
    $activeExternalCompute = Test-ActiveExternalCompute $process $Row $engineTypes $PortRecord
    if ($ownership -eq 'UNKNOWN' -and $activeExternalCompute) { $ownership = 'EXTERNAL_COMPUTE' }
    $nonConflictBasis = $null
    if ($ownership -eq 'UNKNOWN' -and $DriverModel -eq 'WDDM' -and $null -eq $usedMemory -and $hasCompleteProcessMetadata -and $lanePortSafe -and -not $hasComputeEngine -and ($positiveGraphicsContext -or $boundedWddmFallback)) {
        $ownership = 'NON_CONFLICTING_WDDM'
        $nonConflictBasis = if ($positiveGraphicsContext) { 'wddm_non_compute_engine_context' } else { 'wddm_bounded_low_load_fallback' }
    }
    return [ordered]@{
        pid = if ($null -ne $pidKey) { [int64]$pidKey } else { $null }
        pid_key = $pidKey
        process_name = [string]$Row.process_name
        used_memory_mib = $usedMemory
        gpu_uuid = [string]$Row.gpu_uuid
        executable_path = if ($null -ne $process) { Get-Field $process 'executable_path' } else { $null }
        command_line = if ($null -ne $process) { Get-Field $process 'command_line' } else { $null }
        parent_pid = if ($null -ne $process) { Get-Field $process 'parent_pid' } else { $null }
        driver_model = $DriverModel
        gpu_engine_types = $engineTypes
        non_conflict_basis = $nonConflictBasis
        process_lookup_state = $processLookupState
        ownership = $ownership
    }
}

function Get-PortRecord([hashtable]$PortMap, [hashtable]$ProcessMap, [int]$Port, [string]$Root, [string]$LaneId) {
    $row = $PortMap[[string]$Port]
    if ($null -eq $row) { return [ordered]@{ listening = $false; port = $Port; pid = $null; process_name = $null; ownership = $null } }
    $pidKey = Normalize-PidKey (Get-Field $row 'pid')
    $process = if ($null -ne $pidKey) { $ProcessMap[$pidKey] } else { $null }
    $ownership = Test-EstateOwnership $process $Port $Root $LaneId
    return [ordered]@{
        listening = $true
        port = $Port
        pid = if ($null -ne $pidKey) { [int64]$pidKey } else { $null }
        pid_key = $pidKey
        process_name = if ($null -ne $process) { Get-Field $process 'name' } else { $null }
        executable_path = if ($null -ne $process) { Get-Field $process 'executable_path' } else { $null }
        command_line = if ($null -ne $process) { Get-Field $process 'command_line' } else { $null }
        ownership = $ownership
    }
}

function Get-PnpMap([object]$Fixture) {
    $records = @()
    $errors = @()
    $devices = if ($null -ne $Fixture) { @($Fixture) } else { @(Get-PnpDevice -Class Display -ErrorAction SilentlyContinue) }
    foreach ($device in $devices) {
        $friendlyName = Get-Field $device 'FriendlyName'
        $name = Get-Field $device 'Name'
        if ([string]::IsNullOrWhiteSpace([string]$name)) { $name = Get-Field $device 'name' }
        $status = Get-Field $device 'Status'
        $instanceId = Get-Field $device 'InstanceId'
        if ([string]::IsNullOrWhiteSpace([string]$instanceId)) { $instanceId = Get-Field $device 'instance_id' }
        $pnpDeviceId = Get-Field $device 'PNPDeviceID'
        if ([string]::IsNullOrWhiteSpace([string]$pnpDeviceId)) { $pnpDeviceId = Get-Field $device 'pnp_device_id' }
        if ([string]::IsNullOrWhiteSpace([string]$instanceId)) { $instanceId = $pnpDeviceId }
        $problemCode = Get-Field $device 'ProblemCode'
        if ($null -eq $problemCode) { $problemCode = Get-Field $device 'Problem' }
        $configManagerErrorCode = Get-Field $device 'ConfigManagerErrorCode'
        $hardwareIds = @(Get-Field $device 'HardwareID')
        $deviceClass = Get-Field $device 'Class'
        $present = Get-Field $device 'Present'
        if (([string]::IsNullOrWhiteSpace([string]$friendlyName) -and [string]::IsNullOrWhiteSpace([string]$name)) -or [string]::IsNullOrWhiteSpace([string]$status) -or [string]::IsNullOrWhiteSpace([string]$instanceId)) {
            $errors += 'PnP display-device record is missing required FriendlyName/Name, Status, or InstanceId/PNPDeviceID identity/health evidence'
            continue
        }
        $records += [ordered]@{
            friendly_name = if ([string]::IsNullOrWhiteSpace([string]$friendlyName)) { $null } else { [string]$friendlyName }
            name = if ([string]::IsNullOrWhiteSpace([string]$name)) { $null } else { [string]$name }
            status = [string]$status
            instance_id = [string]$instanceId
            pnp_device_id = if ([string]::IsNullOrWhiteSpace([string]$pnpDeviceId)) { $null } else { [string]$pnpDeviceId }
            hardware_ids = $hardwareIds
            class = if ($null -eq $deviceClass) { $null } else { [string]$deviceClass }
            present = $present
            problem_code = $problemCode
            config_manager_error_code = $configManagerErrorCode
        }
    }
    return [ordered]@{ devices = $records; errors = $errors }
}

function Find-PnpRecord([object[]]$Records, [object]$Expected) {
    $identityMatches = @($Records | Where-Object {
        $identityEvidence = @([string]$_.instance_id, [string]$_.pnp_device_id, @($_.hardware_ids) -join ' ') -join ' '
        $identityEvidence -match [regex]::Escape([string]$Expected.pnp_vendor_device_id)
    })
    if ($identityMatches.Count -eq 1) { return $identityMatches[0] }
    if ($identityMatches.Count -gt 1) { return $null }
    $nameMatches = @($Records | Where-Object {
        $nameEvidence = @([string]$_.friendly_name, [string]$_.name) -join ' '
        $nameEvidence -match [regex]::Escape([string]$Expected.pnp_product_pattern)
    })
    if ($nameMatches.Count -eq 1) { return $nameMatches[0] }
    return $null
}

function Invoke-Preflight {
    try {
        $smi = if ($UseNvidiaSmiFixture) { $NvidiaSmiOutput } else { Get-CommandOutput 'nvidia-smi' @('--query-gpu=uuid,name,pci.bus_id,memory.used,memory.free,memory.total,utilization.gpu,temperature.gpu,power.draw,driver_model.current','--format=csv,noheader,nounits') }
        $apps = if ($UseComputeAppsFixture) { $ComputeAppsOutput } else { Get-CommandOutput 'nvidia-smi' @('--query-compute-apps=pid,process_name,used_memory,gpu_uuid','--format=csv,noheader,nounits') }
        $gpuRows = Get-NvidiaRows $smi
        $computeRows = Get-ComputeRows $apps
        $pnpCollection = Get-PnpMap (Read-JsonFixture $PnpOutput)
        $pnp = $pnpCollection.devices
        $processCollection = Get-ProcessMap (Read-JsonFixture $ProcessFixture) $UseProcessFixture
        $processes = $processCollection.processes
        $ports = Get-PortMap (Read-JsonFixture $PortFixture) $UsePortFixture
        $resources = @()
        $globalReasons = @($pnpCollection.errors)
        $globalWarnings = @()
        foreach ($expected in $ExpectedResources) {
            $row = @($gpuRows | Where-Object { $_.uuid -eq $expected.gpu_uuid }) | Select-Object -First 1
            $reasons = @()
            $warnings = @()
            $health = 'OK'
            if ($null -eq $row) {
                $health = 'FAILURE'; $reasons += "expected GPU UUID is missing: $($expected.gpu_uuid)"
            }
            $pnpRow = Find-PnpRecord @($pnp) $expected
            if ($null -eq $pnpRow -or [string]$pnpRow.status -ne 'OK') {
                $health = 'FAILURE'; $reasons += "PnP status is not OK for $($expected.expected_name)"
            }
            if ($null -ne $pnpRow -and [string]::IsNullOrWhiteSpace([string]$pnpRow.instance_id)) {
                $health = 'FAILURE'; $reasons += "PnP instance identity is missing for $($expected.expected_name)"
            }
            $pnpProblemCode = if ($null -ne $pnpRow) { Convert-ToNumber $pnpRow.problem_code } else { $null }
            $pnpConfigManagerErrorCode = if ($null -ne $pnpRow) { Convert-ToNumber $pnpRow.config_manager_error_code } else { $null }
            if (($null -ne $pnpProblemCode -and $pnpProblemCode -ne 0) -or ($null -ne $pnpConfigManagerErrorCode -and $pnpConfigManagerErrorCode -ne 0)) {
                $health = 'FAILURE'; $reasons += "PnP reports an explicit problem code for $($expected.expected_name)"
            }
            if ($null -ne $pnpRow -and $null -ne $pnpRow.present -and -not [bool]$pnpRow.present) {
                $health = 'FAILURE'; $reasons += "PnP reports a phantom or non-present device for $($expected.expected_name)"
            }
            $topologyChanged = $null -ne $row -and $row.pci_bus -ne $expected.prior_observed_pci_bus
            if ($topologyChanged) {
                $warnings += "PCI topology changed for stable UUID $($expected.gpu_uuid): prior observation $($expected.prior_observed_pci_bus), current observation $($row.pci_bus)"
            }
            if ($null -ne $row -and [string]$row.name -ne $expected.expected_name) { $health = 'FAILURE'; $reasons += "GPU name mismatch: expected $($expected.expected_name), observed $($row.name)" }
            $memoryFree = if ($null -ne $row) { Convert-ToNumber $row.memory_free_mib } else { $null }
            $memoryUsed = if ($null -ne $row) { Convert-ToNumber $row.memory_used_mib } else { $null }
            $memoryTotal = if ($null -ne $row) { Convert-ToNumber $row.memory_total_mib } else { $null }
            $util = if ($null -ne $row) { Convert-ToNumber $row.utilization_percent } else { $null }
            $temp = if ($null -ne $row) { Convert-ToNumber $row.temperature_c } else { $null }
            $power = if ($null -ne $row) { Convert-ToNumber $row.power_w } else { $null }
            if ($null -ne $row -and ($null -eq $memoryFree -or $null -eq $memoryTotal -or $null -eq $util)) { $health = 'FAILURE'; $reasons += 'nvidia-smi returned incomplete device telemetry' }
            if ($null -ne $memoryFree -and $memoryFree -lt $expected.minimum_safe_free_mib) { $reasons += "free VRAM $memoryFree MiB is below the accepted floor $($expected.minimum_safe_free_mib) MiB" }
            $port = Get-PortRecord $ports $processes $expected.lane_port $RepoRoot $expected.lane_id
            $gpuProcesses = @($computeRows | Where-Object { $_.gpu_uuid -eq $expected.gpu_uuid } | ForEach-Object { Get-ProcessRecord $_ $processes $expected.lane_port $RepoRoot $expected.lane_id ([string]$row.driver_model) $util $power $port $UseProcessFixture })
            $material = $false
            $unknownComputeOwnership = $false
            $conflictingExternalCompute = $false
            foreach ($proc in $gpuProcesses) {
                if ($proc.ownership -eq 'UNKNOWN') {
                    $unknownComputeOwnership = $true
                } elseif ($proc.ownership -eq 'EXTERNAL_COMPUTE') {
                    $conflictingExternalCompute = $true
                }
                if ($proc.ownership -ne 'ESTATE_OWNED' -and (($null -ne $util -and $util -ge $MaterialUtilizationPercent) -or ($null -ne $power -and $power -ge $MaterialPowerWatts) -or ($null -ne $proc.used_memory_mib -and $proc.used_memory_mib -ge $MaterialProcessMemoryMiB -and $null -ne $util -and $util -ge 10))) { $material = $true }
            }
            if ($material) { $reasons += "material external compute activity: utilization/power/process memory crossed named preflight thresholds" }
            if ($conflictingExternalCompute) { $reasons += 'external model/CUDA worker is present; conservative preflight blocks the lane' }
            if ($unknownComputeOwnership) { $reasons += 'compute process ownership is UNKNOWN; conservative preflight blocks the lane' }
            if ($port.listening -and $port.ownership -ne 'ESTATE_OWNED') { $reasons += "lane port $($expected.lane_port) is occupied by $($port.ownership) PID $($port.pid)" }
            $ready = ($health -eq 'OK' -and $null -ne $memoryFree -and $memoryFree -ge $expected.minimum_safe_free_mib -and -not $material -and -not $conflictingExternalCompute -and -not $unknownComputeOwnership -and (-not $port.listening -or $port.ownership -eq 'ESTATE_OWNED'))
            if (-not $ready -and $health -eq 'OK' -and $reasons.Count -eq 0) { $reasons += 'lane is not ready under the conservative preflight policy' }
            $resources += [ordered]@{
                resource_id = $expected.resource_id; gpu_uuid = $expected.gpu_uuid; name = if ($null -ne $row) { [string]$row.name } else { $null }; pci_bus = if ($null -ne $row) { [string]$row.pci_bus } else { $null }; prior_observed_pci_bus = $expected.prior_observed_pci_bus; pci_topology_changed = $topologyChanged; driver_model = if ($null -ne $row) { [string]$row.driver_model } else { $null }; health = $health; pnp_status = if ($null -ne $pnpRow) { [string]$pnpRow.status } else { 'MISSING' }; pnp_friendly_name = if ($null -ne $pnpRow) { $pnpRow.friendly_name } else { $null }; pnp_name = if ($null -ne $pnpRow) { $pnpRow.name } else { $null }; pnp_instance_id = if ($null -ne $pnpRow) { [string]$pnpRow.instance_id } else { $null }; pnp_device_id = if ($null -ne $pnpRow) { $pnpRow.pnp_device_id } else { $null }; pnp_class = if ($null -ne $pnpRow) { $pnpRow.class } else { $null }; pnp_present = if ($null -ne $pnpRow) { $pnpRow.present } else { $null }; pnp_problem_code = $pnpProblemCode; pnp_config_manager_error_code = $pnpConfigManagerErrorCode; nvml_visible = ($null -ne $row); memory_used_mib = $memoryUsed; memory_free_mib = $memoryFree; memory_total_mib = $memoryTotal; minimum_safe_free_mib = $expected.minimum_safe_free_mib; utilization_percent = $util; temperature_c = $temp; power_w = $power; lane_id = $expected.lane_id; lane_port = $expected.lane_port; lane_port_owner = $port; gpu_engine_collection = $processCollection.gpu_engine_collection; compute_processes = $gpuProcesses; material_external_load = $material; conflicting_external_compute = $conflictingExternalCompute; unknown_compute_ownership = $unknownComputeOwnership; ready = $ready; warnings = $warnings; reasons = $reasons
            }
            $globalWarnings += $warnings
            if ($health -ne 'OK') { $globalReasons += $reasons }
            elseif (-not $ready) { $globalReasons += $reasons }
        }
        $status = if ($pnpCollection.errors.Count -gt 0 -or @($resources | Where-Object { $_.health -ne 'OK' }).Count -gt 0) { 'GPU_HEALTH_FAILURE' } elseif ($globalReasons.Count -gt 0) { 'PRECHECK_BLOCKED' } else { 'PASS' }
        return [ordered]@{ status = $status; timestamp = (Get-Date).ToUniversalTime().ToString('o'); host = $env:COMPUTERNAME; resources = $resources; warnings = @($globalWarnings | Select-Object -Unique); reasons = @($globalReasons | Select-Object -Unique); policy = [ordered]@{ canonical_identity = 'host_id + NVIDIA UUID'; pci_topology = 'observational; a change is warned and recorded but is not an identity or health failure'; material_utilization_percent = $MaterialUtilizationPercent; material_power_watts = $MaterialPowerWatts; material_process_memory_mib = $MaterialProcessMemoryMiB; note = 'VRAM residency alone is not material; active compute and conflicting lane ports block acceptance.' }; exit_code = switch ($status) { 'PASS' { $ExitPass } 'PRECHECK_BLOCKED' { $ExitBlocked } 'GPU_HEALTH_FAILURE' { $ExitHealthFailure } default { $ExitToolError } } }
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
        foreach ($warning in $resource.warnings) { Write-Output "  Warning:     $warning" }
        foreach ($reason in $resource.reasons) { Write-Output "  Reason:      $reason" }
    }
    Write-Output "`nRESULT: $($result.status)"
    foreach ($reason in $result.reasons) { Write-Output "- $reason" }
}
exit ([int]$result.exit_code)
