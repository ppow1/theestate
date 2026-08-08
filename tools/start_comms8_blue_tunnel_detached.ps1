$arguments = @(
    '-N', '-T', '-i', 'C:\Users\wille\.ssh\id_ed25519',
    '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
    '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
    '-o', 'ConnectTimeout=10',
    '-o', 'UserKnownHostsFile=C:\Users\wille\.ssh\known_hosts',
    '-o', 'GlobalKnownHostsFile=NUL',
    '-R', '127.0.0.1:11808:127.0.0.1:11809', 'root@64.227.21.54'
)
$process = Start-Process -FilePath 'C:\Windows\System32\OpenSSH\ssh.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru
Write-Output ("SSH_PID={0}" -f $process.Id)
