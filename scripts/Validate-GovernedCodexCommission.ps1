param(
  [Parameter(Mandatory = $true, Position = 0)]
  [Alias('JsonPath', 'Path')]
  [string]$RequestPath,
  [switch]$Json
)

try { CLS } catch { }

$ErrorActionPreference = 'Stop'
$script:Errors = [System.Collections.Generic.List[string]]::new()

function Add-ValidationError([string]$Message) {
  if (-not [string]::IsNullOrWhiteSpace($Message)) { [void]$script:Errors.Add($Message) }
}

function Emit-Result([bool]$Valid, [int]$ExitCode) {
  $result = [ordered]@{
    valid = $Valid
    request_path = $RequestPath
    provider_id = if ($null -ne $request) { [string]$request.provider_id } else { $null }
    adapter_id = if ($null -ne $request) { [string]$request.adapter_id } else { $null }
    errors = @($script:Errors)
    validation_only = $true
    provider_invoked = $false
    lifecycle_mutated = $false
  }
  if ($Json) {
    $result | ConvertTo-Json -Depth 8 -Compress
  } else {
    if ($Valid) { Write-Output 'VALID: governed Codex commission request passed read-only validation.' }
    else { Write-Output ('INVALID: ' + $script:Errors.Count + ' validation error(s) detected.') }
    foreach ($errorItem in $script:Errors) { Write-Output ('- ' + $errorItem) }
    Write-Output ('Provider invoked: ' + $result.provider_invoked)
    Write-Output ('Lifecycle mutated: ' + $result.lifecycle_mutated)
  }
  exit $ExitCode
}

function Property-Value($Object, [string]$Name) {
  if ($null -eq $Object) { return $null }
  return $Object.PSObject.Properties[$Name].Value
}

function Has-Text($Value) {
  return $null -ne $Value -and -not [string]::IsNullOrWhiteSpace([string]$Value)
}

function NonEmpty-List($Value) {
  return $null -ne $Value -and $Value -is [System.Array] -and @($Value).Count -gt 0
}

if (-not (Test-Path -LiteralPath $RequestPath -PathType Leaf)) {
  Add-ValidationError 'request JSON path does not exist or is not a file'
  Emit-Result $false 1
}

try {
  $request = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
  if ($request -is [System.Array] -or $null -eq $request) { throw 'request JSON must contain one object' }
} catch {
  Add-ValidationError ('malformed request JSON: ' + $_.Exception.Message)
  Emit-Result $false 2
}

$requiredFields = @(
  'commission_id', 'grace_objective_id', 'capability_inquiry_id',
  'helen_assessment_reference', 'ptm_dependency_reference', 'dispatch_id',
  'provider_id', 'adapter_id', 'adapter_version', 'classification',
  'repository_root', 'source_commit', 'sandbox_mode', 'authorized_read_paths',
  'authorized_write_paths', 'prohibited_paths', 'exact_expected_outputs',
  'acceptance_criteria', 'validation_commands', 'timeout_seconds',
  'cancellation_state', 'steward_authorization_reference',
  'traffic_controller_authorization_reference', 'decision_reference',
  'boundary_review_reference', 'requested_capabilities', 'evidence'
)
foreach ($field in $requiredFields) {
  $value = Property-Value $request $field
  if (-not (Has-Text $value) -and -not (NonEmpty-List $value)) {
    Add-ValidationError "required field is missing: $field"
  }
}

if ([string]$request.provider_id -ne 'codex.execution.cli') { Add-ValidationError 'provider_id must be codex.execution.cli' }
if ([string]$request.adapter_id -ne 'codex-cli-execution-adapter') { Add-ValidationError 'adapter_id does not match the registered canonical adapter' }
if ([string]$request.adapter_version -ne '1.0.0') { Add-ValidationError 'adapter_version must be 1.0.0 for the registered canonical adapter' }

$profileSupplied = Has-Text (Property-Value $request 'codex_provider_profile')
if ($profileSupplied -and (@('codex-cli-openai', 'codex-cli-ollama') -notcontains [string]$request.codex_provider_profile)) {
  Add-ValidationError 'codex_provider_profile is not an allowed local Codex profile'
}
if (Has-Text (Property-Value $request 'approval_policy') -and [string]$request.approval_policy -ne 'never') {
  Add-ValidationError 'approval_policy must be never for bridge automation'
}
if (NonEmpty-List (Property-Value $request 'bypass_flags')) { Add-ValidationError 'bypass flags are prohibited' }
foreach ($booleanField in @('cloud_allowed', 'cloud_apply_requested', 'cloud_dispatch_requested', 'danger_full_access_requested')) {
  if ($request.PSObject.Properties.Name -contains $booleanField -and [bool](Property-Value $request $booleanField)) {
    Add-ValidationError "$booleanField is prohibited"
  }
}

$supportedCapabilities = @('repository_implementation', 'code_review', 'documentation_draft', 'test_execution', 'bounded_repository_work')
foreach ($capability in @($request.requested_capabilities)) {
  if ([string]::IsNullOrWhiteSpace([string]$capability) -or $supportedCapabilities -notcontains [string]$capability) {
    Add-ValidationError "unsupported capability: $capability"
  }
}

if (@('read-only', 'workspace-write') -notcontains [string]$request.sandbox_mode) { Add-ValidationError 'sandbox_mode must be read-only or workspace-write' }
if ([string]$request.sandbox_mode -eq 'danger-full-access') { Add-ValidationError 'danger-full-access is prohibited' }
if ([string]$request.cancellation_state -notin @('not_requested', 'requested')) { Add-ValidationError 'cancellation_state must be not_requested or requested' }
if ([string]$request.cancellation_state -eq 'requested') { Add-ValidationError 'cancellation requested: do not execute this commission' }
if ($request.unrestricted_shell_authority -ne $false) { Add-ValidationError 'unrestricted shell authority must be false' }
if ($request.automatic_merge_authority -ne $false) { Add-ValidationError 'automatic merge authority must be false' }
if ($request.autonomous_institutional_acceptance_authority -ne $false) { Add-ValidationError 'autonomous institutional-acceptance authority must be false' }

foreach ($referenceField in @('steward_authorization_reference', 'traffic_controller_authorization_reference', 'decision_reference', 'boundary_review_reference')) {
  if ([string]::IsNullOrWhiteSpace([string]$request.$referenceField)) { Add-ValidationError "authorization or decision reference is required: $referenceField" }
}
if (@($request.acceptance_criteria).Count -eq 0) { Add-ValidationError 'at least one acceptance criterion is required' }
if (@($request.validation_commands).Count -eq 0) { Add-ValidationError 'at least one validation command is required' }
if (@($request.exact_expected_outputs).Count -eq 0) { Add-ValidationError 'at least one exact expected output is required' }
if (@($request.authorized_read_paths).Count -eq 0) { Add-ValidationError 'at least one authorized read path is required' }
if ([string]$request.sandbox_mode -eq 'workspace-write' -and @($request.authorized_write_paths).Count -eq 0) { Add-ValidationError 'workspace-write requires explicit authorized write paths' }
$timeoutValue = 0
$timeoutParsed = [int]::TryParse([string]$request.timeout_seconds, [ref]$timeoutValue)
if (-not $timeoutParsed -or $timeoutValue -le 0) { Add-ValidationError 'timeout_seconds must be a positive integer' }

function Normalize-RelativePath([string]$RawPath) {
  return (($RawPath -replace '\\', '/') -replace '^\./', '').Trim('/')
}
function Is-AbsolutePath([string]$RawPath) {
  return [IO.Path]::IsPathRooted($RawPath) -or $RawPath -match '^[A-Za-z]:[\\/]'
}
function Has-ParentSegment([string]$NormalizedPath) {
  return (@($NormalizedPath -split '/') -contains '..')
}

# These roots mirror the existing runtime writers in:
# codex_bridge_execution_provider_adapter.py,
# execution_provider_adapter_runtime.py, execution_result_reconciliation_runtime.py,
# grace_helen_engineering_composition.py, engineering_capability_enablement.py,
# and execution_dispatch.py.  A root is never itself an authorized write scope.
$canonicalRuntimeRoots = @(
  'runtime/engineering_adapter_receipts',
  'runtime/execution_adapters/requests',
  'runtime/execution_adapters/results',
  'runtime/execution_adapters/reconciliation',
  'runtime/execution_adapters/reports',
  'runtime/grace_helen_engineering/capability_enablement',
  'runtime/grace_helen_engineering/engineering_commissions',
  'runtime/grace_helen_engineering/engineering_authorizations',
  'runtime/grace_helen_engineering/engineering_validations',
  'runtime/grace_helen_engineering/engineering_completions',
  'runtime/grace_helen_engineering/grace_receipts',
  'runtime/operations/grace/objectives',
  'runtime/operations/grace/actions',
  'runtime/operations/grace/escalations',
  'runtime/operations/grace/closures',
  'runtime/operations/grace/status',
  'runtime/operations/grace/objective_states',
  'runtime/execution_dispatch'
)
function Get-CanonicalRuntimeRoot([string]$Scope) {
  foreach ($root in $canonicalRuntimeRoots) {
    if ($Scope -eq $root -or $Scope.StartsWith($root.TrimEnd('/') + '/')) { return $root }
  }
  return $null
}
function Test-NarrowCanonicalRuntimeScope([string]$Scope, [string]$Root) {
  if ([string]::IsNullOrWhiteSpace($Root) -or $Scope -eq $Root) { return $false }
  $suffix = $Scope.Substring($Root.Length).Trim('/')
  $segments = @($suffix -split '/' | Where-Object { $_ })
  if ($segments.Count -eq 0) { return $false }
  $leaf = [string]$segments[-1]
  # Canonical evidence is normally an exact JSON/Markdown/JSONL record.  A
  # single commission/dispatch/adapter directory is also permitted when the
  # caller has narrowed it to that identifier rather than the shared root.
  if ($leaf -match '\.(json|jsonl|md)$') { return $true }
  return ($segments.Count -eq 1 -and $leaf -match '^(commission|dispatch|adapter|eng(auth|comp|val)|cap|grace|objective|reconciliation)[A-Za-z0-9._-]*$')
}

$writeScopes = @($request.authorized_write_paths | ForEach-Object { Normalize-RelativePath ([string]$_) } | Where-Object { $_ })
$prohibited = @('.git', '.codex', 'archive') + @($request.prohibited_paths | ForEach-Object { Normalize-RelativePath ([string]$_) } | Where-Object { $_ })
foreach ($scope in $writeScopes) {
  if ($scope -eq '.') { Add-ValidationError 'authorized write path is too broad: repository root is not an allowed write scope' }
  if (Is-AbsolutePath $scope -or Has-ParentSegment $scope) { Add-ValidationError "authorized write path must be repository-relative and traversal-free: $scope" }
  if ($scope -eq 'runtime' -or $scope.StartsWith('runtime/')) {
    $runtimeRoot = Get-CanonicalRuntimeRoot $scope
    if ([string]::IsNullOrWhiteSpace($runtimeRoot)) {
      Add-ValidationError "runtime write path is not a recognized canonical evidence location: $scope"
    } elseif (-not (Test-NarrowCanonicalRuntimeScope $scope $runtimeRoot)) {
      Add-ValidationError "runtime write scope must be a narrow commission-specific file or directory below '$runtimeRoot': $scope"
    }
  }
  foreach ($blocked in $prohibited) {
    if ($scope -eq $blocked -or $scope.StartsWith($blocked.TrimEnd('/') + '/')) { Add-ValidationError "authorized write path overlaps prohibited path '$blocked': $scope" }
  }
}
foreach ($output in @($request.exact_expected_outputs)) {
  $rawOutput = [string]$output
  $normalizedOutput = Normalize-RelativePath $rawOutput
  if ([string]::IsNullOrWhiteSpace($rawOutput)) { Add-ValidationError 'exact expected output cannot be empty'; continue }
  if (Is-AbsolutePath $rawOutput) { Add-ValidationError "expected output must be repository-relative: $rawOutput" }
  if (Has-ParentSegment $normalizedOutput) { Add-ValidationError "expected output cannot contain .. traversal: $rawOutput" }
  if ($normalizedOutput -eq '.') { Add-ValidationError "expected output must name a file below the repository root: $rawOutput" }
  if (-not (@($writeScopes | Where-Object { $normalizedOutput -eq $_ -or $normalizedOutput.StartsWith($_.TrimEnd('/') + '/') }).Count -gt 0)) { Add-ValidationError "expected output is outside authorized write scopes: $rawOutput" }
}

$evidence = $request.evidence
foreach ($evidenceField in @('observed_at', 'expires_at')) {
  if ([string]::IsNullOrWhiteSpace([string]$evidence.$evidenceField)) { Add-ValidationError "evidence timestamp is required: evidence.$evidenceField" }
}
$observed = $null; $expires = $null
try { $observed = [DateTimeOffset]::Parse([string]$evidence.observed_at); $expires = [DateTimeOffset]::Parse([string]$evidence.expires_at) } catch { Add-ValidationError 'evidence timestamps must be valid ISO-8601 timestamps' }
if ($null -ne $expires -and $expires -le [DateTimeOffset]::UtcNow) { Add-ValidationError 'evidence expires_at is already expired' }
if ($null -ne $observed -and $null -ne $expires -and $expires -le $observed) { Add-ValidationError 'evidence expires_at must be later than observed_at' }
foreach ($evidenceReferenceField in @('qualification_references', 'health_references', 'availability_references', 'capacity_references', 'authorization_references')) {
  if (@($evidence.$evidenceReferenceField).Count -eq 0) { Add-ValidationError "evidence reference list is required: evidence.$evidenceReferenceField" }
}

if ($script:Errors.Count -gt 0) { Emit-Result $false 1 }
Emit-Result $true 0
