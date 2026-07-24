CLS

$ErrorActionPreference = "Stop"

Write-Host "" 
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ESTATE VISUAL TURNTABLE PROJECT INSTALL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$DefaultRepoCandidates = @(
    "A:\theestate",
    "A:\AI\Projects\theestate",
    "A:\AI\Projects\Estate\theestate",
    "$env:USERPROFILE\Documents\GitHub\theestate",
    "$env:USERPROFILE\source\repos\theestate"
)

$RepoRoot = $DefaultRepoCandidates |
    Where-Object { Test-Path (Join-Path $_ ".git") } |
    Select-Object -First 1

if (-not $RepoRoot) {
    $RepoRoot = Read-Host "Enter the full path to your local theestate repository"
}

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "The selected folder is not a Git repository: $RepoRoot"
}

$ScriptRoot = Split-Path -Parent $PSScriptRoot
$Destination = Join-Path $RepoRoot "collaboration\projects\in_progress\visual_turntable_pipeline"
$AIDestination = "A:\AI\Projects\Estate\Visual-Turntable-Pipeline"

Write-Host "Repository: $RepoRoot" -ForegroundColor Green
Write-Host "Repository destination: $Destination" -ForegroundColor Green
Write-Host "A: working mirror: $AIDestination" -ForegroundColor Green
Write-Host ""

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
New-Item -ItemType Directory -Path $AIDestination -Force | Out-Null

Copy-Item -Path (Join-Path $ScriptRoot "*") -Destination $Destination -Recurse -Force
Copy-Item -Path (Join-Path $ScriptRoot "*") -Destination $AIDestination -Recurse -Force

# Prevent the installer from recursively copying a nested copy if rerun from inside the destination.
$NestedRepoCopy = Join-Path $Destination "visual_turntable_pipeline"
$NestedAICopy = Join-Path $AIDestination "visual_turntable_pipeline"
if (Test-Path $NestedRepoCopy) { Remove-Item $NestedRepoCopy -Recurse -Force }
if (Test-Path $NestedAICopy) { Remove-Item $NestedAICopy -Recurse -Force }

Write-Host "Package copied successfully." -ForegroundColor Green
Write-Host ""

Set-Location $RepoRoot

git status --short
Write-Host ""

$Commit = Read-Host "Commit and push this project package now? Type YES to continue"
if ($Commit -eq "YES") {
    git add -- "collaboration/projects/in_progress/visual_turntable_pipeline"
    git commit -m "Capture visual turntable pipeline project"
    git push
    Write-Host "Repository committed and pushed." -ForegroundColor Green
}
else {
    Write-Host "Files are staged locally only if you run git add later; no commit or push was performed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "DONE" -ForegroundColor Cyan
Write-Host "Repository copy: $Destination"
Write-Host "A: mirror:       $AIDestination"
