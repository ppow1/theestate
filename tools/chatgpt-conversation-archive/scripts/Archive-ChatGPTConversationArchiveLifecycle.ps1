function ConvertTo-ArchiveComparableCommandLine {
    param([AllowNull()][string]$CommandLine)
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { return '' }
    return (($CommandLine -replace '"','').Replace('\','/')).ToLowerInvariant()
}

function Get-ArchiveProfileNeedle {
    param([Parameter(Mandatory)][string]$ProfilePath)
    $full = [IO.Path]::GetFullPath($ProfilePath).TrimEnd('\','/')
    return "--user-data-dir=$($full.Replace('\','/'))".ToLowerInvariant()
}

function Get-ArchiveProfileProcesses {
    param(
        [Parameter(Mandatory)][string]$ProfilePath,
        [object[]]$Processes
    )
    if ($null -eq $Processes) {
        $Processes = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'")
    }
    $needle = Get-ArchiveProfileNeedle $ProfilePath
    @($Processes | Where-Object { (ConvertTo-ArchiveComparableCommandLine $_.CommandLine).Contains($needle) })
}

function Get-ArchiveMainBrowserProcesses {
    param(
        [Parameter(Mandatory)][string]$ProfilePath,
        [object[]]$Processes
    )
    $matched = @(Get-ArchiveProfileProcesses -ProfilePath $ProfilePath -Processes $Processes)
    @($matched | Where-Object { -not (ConvertTo-ArchiveComparableCommandLine $_.CommandLine).Contains('--type=') })
}

function Get-ArchiveBrowserWindows {
    param(
        [Parameter(Mandatory)][string]$ProfilePath,
        [object[]]$Processes
    )
    $main = @(Get-ArchiveMainBrowserProcesses -ProfilePath $ProfilePath -Processes $Processes)
    $windows = foreach ($item in $main) {
        $handle = $item.MainWindowHandle
        if ($null -eq $handle -and $item.ProcessId) {
            $live = Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue
            if ($live) { $handle = $live.MainWindowHandle }
        }
        if ($handle -and [int64]$handle -ne 0) {
            [pscustomobject]@{ ProcessId = $item.ProcessId; CommandLine = $item.CommandLine; MainWindowHandle = $handle }
        }
    }
    @($windows)
}

function Test-ArchiveProfileLocksReleased {
    param([Parameter(Mandatory)][string]$ProfilePath)
    $lockFiles = @('SingletonLock','SingletonCookie','SingletonSocket') | ForEach-Object { Join-Path $ProfilePath $_ }
    -not ($lockFiles | Where-Object { Test-Path -LiteralPath $_ })
}
