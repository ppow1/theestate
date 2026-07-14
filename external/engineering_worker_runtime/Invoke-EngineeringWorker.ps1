CLS
$ErrorActionPreference = 'Stop'
$runtime = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $runtime 'engineering_worker_runtime.py') @args
