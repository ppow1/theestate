CLS
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$Canons = @(
    @{
        Id = 'WP-4111'
        Directory = 'WP-4111_SERIES_Height_Proportion_and_Scale_Reference_System'
        ExpectedPartCount = 7
        ExpectedSha256 = '2c675f77d9807b79955dff983801a80d1c16e3b6578573d73f5982f48f4093e3'
    },
    @{
        Id = 'WP-4112'
        Directory = 'WP-4112_SERIES_Measurement_Variant_Review_Workflow'
        ExpectedPartCount = 8
        ExpectedSha256 = '08b1f92f844d7c5f280db6f87681021cba702863c1e3b99c759e6e4d3d45b43a'
    }
)

foreach ($Canon in $Canons) {
    $Directory = Join-Path $Root $Canon.Directory
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        throw "$($Canon.Id): fragment directory not found: $Directory"
    }

    $Parts = @(Get-ChildItem -LiteralPath $Directory -File -Filter '*.md' |
        Where-Object { $_.Name -match '(?i)part[-_ ]?[0-9]+' } |
        Sort-Object Name)

    if ($Parts.Count -ne $Canon.ExpectedPartCount) {
        throw "$($Canon.Id): expected $($Canon.ExpectedPartCount) parts, found $($Parts.Count)."
    }

    $Builder = New-Object System.Text.StringBuilder
    foreach ($Part in $Parts) {
        [void]$Builder.Append([System.IO.File]::ReadAllText($Part.FullName))
    }

    $Output = Join-Path $Directory ($Canon.Directory + '_RUNTIME_CANON.md')
    [System.IO.File]::WriteAllText($Output, $Builder.ToString(), $Utf8NoBom)

    $ActualSha256 = (Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualSha256 -ne $Canon.ExpectedSha256) {
        Remove-Item -LiteralPath $Output -Force
        throw "$($Canon.Id): SHA-256 mismatch. Expected $($Canon.ExpectedSha256); got $ActualSha256."
    }

    Write-Host "$($Canon.Id): reconstructed and verified -> $Output"
}
