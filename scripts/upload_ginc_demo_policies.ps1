param(
    [string]$ApiBase = 'http://localhost:8000'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policyDir = Join-Path $repoRoot 'data\company\g-inc'
$health = Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 5
if ($health.status -notin @('ok', 'degraded')) {
    throw "API health is '$($health.status)'. Start the backend before uploading demo policies."
}

$registered = Invoke-RestMethod -Uri "$ApiBase/api/v1/company/documents" -TimeoutSec 10
$policies = Get-ChildItem -LiteralPath $policyDir -Filter '*-DRAFT.md' -File
if ($policies.Count -eq 0) {
    throw "No G Inc policy drafts were found in $policyDir"
}

foreach ($policy in $policies) {
    if (@($registered | Where-Object { $_.filename -eq $policy.Name }).Count -gt 0) {
        Write-Host "Already registered; skipping $($policy.Name)"
        continue
    }
    Write-Host "Indexing fictional company policy $($policy.Name)"
    & curl.exe --silent --show-error --fail-with-body -X POST `
        "$ApiBase/api/v1/company/documents/upload" `
        -F "file=@$($policy.FullName);type=text/markdown" `
        -F "title=$([System.IO.Path]::GetFileNameWithoutExtension($policy.Name))"
    if ($LASTEXITCODE -ne 0) {
        throw "Upload failed for $($policy.Name) (curl exit $LASTEXITCODE). Check API logs and retry."
    }
}

Write-Host "\nG Inc demo policies uploaded to the separate company collection. Open Company Review in the app."
