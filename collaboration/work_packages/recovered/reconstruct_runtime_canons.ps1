CLS
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

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
        ExpectedSha256 = '08b1f92f844