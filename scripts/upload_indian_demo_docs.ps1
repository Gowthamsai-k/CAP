param(
    [string]$ApiBase = 'http://localhost:8000'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$corpusDir = Join-Path $repoRoot 'data\legal\india\dpdp'
$manifestPath = Join-Path $corpusDir 'download_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Missing $manifestPath. Run scripts\download_indian_demo_docs.ps1 first."
}

$health = Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 5
if ($health.status -ne 'ok') {
    throw "API health is '$($health.status)'. Start the backend and check $ApiBase/health before upload."
}

$registered = Invoke-RestMethod -Uri "$ApiBase/api/v1/documents" -TimeoutSec 10
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($document in $manifest) {
    $filePath = Join-Path $corpusDir $document.filename
    if (-not (Test-Path -LiteralPath $filePath)) {
        throw "Missing downloaded file: $filePath"
    }
    if (@($registered | Where-Object { $_.filename -eq $document.filename }).Count -gt 0) {
        Write-Host "Already registered; skipping $($document.filename)"
        continue
    }

    $formArgs = @(
        '--silent', '--show-error', '--fail-with-body',
        '-X', 'POST', "$ApiBase/api/v1/documents/upload",
        '-F', "file=@$filePath;type=application/pdf",
        '-F', "title=$($document.title)",
        '-F', "jurisdiction=$($document.jurisdiction)",
        '-F', "country=$($document.country)",
        '-F', "domain=$($document.domain)",
        '-F', "authority=$($document.authority)",
        '-F', "document_type=$($document.document_type)",
        '-F', "source_url=$($document.source_url)",
        '-F', "version=$($document.version)",
        '-F', "publication_date=$($document.publication_date)",
        '-F', "document_status=$($document.document_status)"
    )
    Write-Host "Indexing $($document.title)"
    & curl.exe @formArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Upload failed for $($document.filename) (curl exit $LASTEXITCODE). Check API logs and try again."
    }
}

Write-Host "\nLegal demo corpus uploaded. Review documents at $ApiBase/api/v1/documents"
Write-Host 'The G Inc company drafts are separate and are not uploaded to the legal collection.'
