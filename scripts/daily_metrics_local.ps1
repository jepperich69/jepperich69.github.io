# daily_metrics_local.ps1
# Run by the Windows scheduled task JR_Website_DailyMetrics (daily 07:00, catches up after sleep).
# Google Scholar refuses GitHub's servers, so the laptop fetches it and pushes the result.
# Scopus and OpenAlex are fetched by the GitHub Action as well; update_metrics.py merges into the
# existing metrics.json, so the two runs never erase each other's values.
# Only assets/metrics.json and docs/assets/metrics.json are committed; other work in the folder is untouched.

$ErrorActionPreference = 'Continue'
$site = Split-Path -Parent $PSScriptRoot
$logDir = Join-Path $env:LOCALAPPDATA 'JR_Website'
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir 'daily_metrics.log'
$python = 'C:\Users\rich\AppData\Local\miniconda3\python.exe'
$files = @('assets/metrics.json', 'docs/assets/metrics.json')

function Write-Log([string]$msg) {
    Add-Content -Path $log -Value ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $msg)
}

Set-Location $site
Write-Log '--- start'
git pull --rebase --autostash -q 2>&1 | ForEach-Object { Write-Log ('pull: ' + $_) }
& $python (Join-Path $PSScriptRoot 'update_metrics.py') 2>&1 | ForEach-Object { Write-Log $_ }

git add -- $files
git diff --cached --quiet -- $files
if ($LASTEXITCODE -ne 0) {
    git commit -q -m 'chore: daily Google Scholar update (laptop)' -- $files 2>&1 | ForEach-Object { Write-Log ('commit: ' + $_) }
    git push -q 2>&1 | ForEach-Object { Write-Log ('push: ' + $_) }
    if ($LASTEXITCODE -ne 0) {
        # GitHub moved on in the meantime: rebase once and retry.
        git pull --rebase --autostash -q 2>&1 | ForEach-Object { Write-Log ('pull retry: ' + $_) }
        git push -q 2>&1 | ForEach-Object { Write-Log ('push retry: ' + $_) }
    }
    Write-Log ('pushed, exit ' + $LASTEXITCODE)
} else {
    Write-Log 'no change'
}
Write-Log '--- end'
