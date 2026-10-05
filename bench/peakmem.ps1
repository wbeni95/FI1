# Runs a command and reports its wall time and peak working set (sampled every 100 ms).
# Usage: powershell -File peakmem.ps1 <exe> <args...>
param([Parameter(Mandatory = $true)][string]$Exe, [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
$sw = [Diagnostics.Stopwatch]::StartNew()
$quoted = ($Rest | ForEach-Object { '"' + $_ + '"' }) -join ' '
$p = Start-Process -FilePath $Exe -ArgumentList $quoted -NoNewWindow -PassThru
$peak = 0
while (-not $p.HasExited) {
    try { $p.Refresh(); if ($p.PeakWorkingSet64 -gt $peak) { $peak = $p.PeakWorkingSet64 } } catch {}
    Start-Sleep -Milliseconds 100
}
$sw.Stop()
"exit {0}  wall {1:N1} s  peak working set {2:N0} MB" -f $p.ExitCode, $sw.Elapsed.TotalSeconds, ($peak / 1MB)
