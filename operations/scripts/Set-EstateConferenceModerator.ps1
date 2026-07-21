CLS
$Resident = $null
$Verify = $false
for ($Index = 0; $Index -lt $args.Count; $Index++) {
    if ($args[$Index] -eq "-Verify") { $Verify = $true }
    elseif ($args[$Index] -eq "-Resident" -and $Index + 1 -lt $args.Count) { $Index++; $Resident = $args[$Index] }
    else { throw "Unknown or incomplete argument: $($args[$Index])" }
}
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Command = @((Join-Path $RepositoryRoot "scripts\set_estate_conference_moderator.py"), "--root", $RepositoryRoot)
if ($Verify) { $Command += "--verify" }
elseif ($Resident) { $Command += @("--resident", $Resident) }
else { throw "Supply -Resident <name-or-canonical-id> or -Verify." }
& python @Command
if ($LASTEXITCODE -ne 0) { throw "Conference moderator update failed closed." }
