$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$targetDir = Join-Path $repoRoot 'data\legal\india\dpdp'
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

# This is a focused DPDP demo corpus, not a complete collection of Indian law.
# Every URL below points to India Code, MeitY, or the Official Gazette.
$documents = @(
    @{
        filename = 'dpdp_act_2023_india_code.pdf'
        title = 'Digital Personal Data Protection Act, 2023'
        # India Code can intermittently time out; MeitY hosts the same official Act.
        urls = @(
            'https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf',
            'https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf'
        )
        authority = 'Legislative Department, Ministry of Law and Justice'
        document_type = 'act'
        version = 'Act No. 22 of 2023; India Code text as available from the official record'
        publication_date = '2023-08-11'
        status = 'phased'
    },
    @{
        filename = 'dpdp_rules_2025_gsr_846e.pdf'
        title = 'Digital Personal Data Protection Rules, 2025 (G.S.R. 846(E))'
        urls = @('https://egazette.gov.in/WriteReadData/2025/267650.pdf')
        authority = 'Ministry of Electronics and Information Technology, Government of India'
        document_type = 'rules'
        version = 'G.S.R. 846(E), 13 November 2025; read with G.S.R. 892(E) corrigendum'
        publication_date = '2025-11-13'
        status = 'phased'
    },
    @{
        filename = 'dpdp_act_commencement_gsr_843e.pdf'
        title = 'Commencement notification for the DPDP Act (G.S.R. 843(E))'
        urls = @('https://egazette.gov.in/WriteReadData/2025/267647.pdf')
        authority = 'Ministry of Electronics and Information Technology, Government of India'
        document_type = 'commencement_notification'
        version = 'G.S.R. 843(E), 13 November 2025'
        publication_date = '2025-11-13'
        status = 'notified'
    },
    @{
        filename = 'dpdp_rules_corrigendum_gsr_892e.pdf'
        title = 'Corrigendum to the DPDP Rules, 2025 (G.S.R. 892(E))'
        urls = @('https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf')
        authority = 'Ministry of Electronics and Information Technology, Government of India'
        document_type = 'corrigendum'
        version = 'G.S.R. 892(E), Gazette publication 11 December 2025'
        publication_date = '2025-12-11'
        status = 'corrective'
    }
)

$manifest = @()
foreach ($document in $documents) {
    $destination = Join-Path $targetDir $document.filename
    $downloadedFrom = $null
    Write-Host "Downloading $($document.title)"
    $errors = @()
    foreach ($url in $document.urls) {
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            $temporaryPath = "$destination.part"
            try {
                Invoke-WebRequest -Uri $url -OutFile $temporaryPath -MaximumRedirection 8 -TimeoutSec 180
                $bytes = [System.IO.File]::ReadAllBytes($temporaryPath)
                if ($bytes.Length -lt 5 -or [System.Text.Encoding]::ASCII.GetString($bytes[0..4]) -ne '%PDF-') {
                    throw 'The response is not a PDF file.'
                }
                Move-Item -LiteralPath $temporaryPath -Destination $destination -Force
                $downloadedFrom = $url
                break
            }
            catch {
                Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
                $errors += "Attempt $attempt from $url`: $($_.Exception.Message)"
                if ($attempt -lt 3) {
                    Start-Sleep -Seconds (5 * $attempt)
                }
            }
        }
        if ($downloadedFrom) { break }
    }
    if (-not $downloadedFrom) {
        throw "Download/validation failed for '$($document.title)' from all configured official URLs. Check network access and retry.`n$($errors -join "`n")"
    }

    $manifest += [ordered]@{
        document_id = [System.IO.Path]::GetFileNameWithoutExtension($document.filename)
        filename = $document.filename
        title = $document.title
        country = 'India'
        jurisdiction = 'IN'
        domain = 'data_privacy'
        source_type = 'legal'
        authority = $document.authority
        document_type = $document.document_type
        source_url = $downloadedFrom
        version = $document.version
        publication_date = $document.publication_date
        effective_from = $null
        effective_to = $null
        document_status = $document.status
        sha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        downloaded_at_utc = [DateTime]::UtcNow.ToString('o')
    }
}

$manifestPath = Join-Path $targetDir 'download_manifest.json'
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Host "\nDownloaded and PDF-validated $($manifest.Count) official documents to: $targetDir"
Write-Host "SHA-256 manifest: $manifestPath"
Write-Host 'Review the phased commencement metadata before treating any provision as currently applicable.'
