#!/usr/bin/env python3
"""Cross-platform script to download and validate the Indian DPDP demo corpus."""
import hashlib
import json
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = REPO_ROOT / "data" / "legal" / "india" / "dpdp"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENTS = [
    {
        "filename": "dpdp_act_2023_india_code.pdf",
        "title": "Digital Personal Data Protection Act, 2023",
        "urls": [
            "https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf",
            "https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf",
        ],
        "authority": "Legislative Department, Ministry of Law and Justice",
        "document_type": "act",
        "version": "Act No. 22 of 2023; India Code text as available from the official record",
        "publication_date": "2023-08-11",
        "status": "phased",
    },
    {
        "filename": "dpdp_rules_2025_gsr_846e.pdf",
        "title": "Digital Personal Data Protection Rules, 2025 (G.S.R. 846(E))",
        "urls": ["https://egazette.gov.in/WriteReadData/2025/267650.pdf"],
        "authority": "Ministry of Electronics and Information Technology, Government of India",
        "document_type": "rules",
        "version": "G.S.R. 846(E), 13 November 2025; read with G.S.R. 892(E) corrigendum",
        "publication_date": "2025-11-13",
        "status": "phased",
    },
    {
        "filename": "dpdp_act_commencement_gsr_843e.pdf",
        "title": "Commencement notification for the DPDP Act (G.S.R. 843(E))",
        "urls": ["https://egazette.gov.in/WriteReadData/2025/267647.pdf"],
        "authority": "Ministry of Electronics and Information Technology, Government of India",
        "document_type": "commencement_notification",
        "version": "G.S.R. 843(E), 13 November 2025",
        "publication_date": "2025-11-13",
        "status": "notified",
    },
    {
        "filename": "dpdp_rules_corrigendum_gsr_892e.pdf",
        "title": "Corrigendum to the DPDP Rules, 2025 (G.S.R. 892(E))",
        "urls": ["https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf"],
        "authority": "Ministry of Electronics and Information Technology, Government of India",
        "document_type": "corrigendum",
        "version": "G.S.R. 892(E), Gazette publication 11 December 2025",
        "publication_date": "2025-12-11",
        "status": "corrective",
    },
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

manifest = []
for doc in DOCUMENTS:
    destination = TARGET_DIR / doc["filename"]
    print(f"Downloading {doc['title']}...")
    downloaded_from = None
    errors = []

    for url in doc["urls"]:
        for attempt in range(1, 4):
            temp_path = destination.with_suffix(".part")
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
                    content = response.read()
                if len(content) < 5 or not content.startswith(b"%PDF-"):
                    raise ValueError("Downloaded response is not a valid PDF file.")
                temp_path.write_bytes(content)
                temp_path.replace(destination)
                downloaded_from = url
                break
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                errors.append(f"Attempt {attempt} from {url}: {e}")
                if attempt < 3:
                    time.sleep(3 * attempt)
        if downloaded_from:
            break

    if not downloaded_from:
        print(f"Warning: Could not download {doc['title']}:\n" + "\n".join(errors), file=sys.stderr)
        continue

    file_bytes = destination.read_bytes()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest().lower()
    manifest.append({
        "document_id": destination.stem,
        "filename": doc["filename"],
        "title": doc["title"],
        "country": "India",
        "jurisdiction": "IN",
        "domain": "data_privacy",
        "source_type": "legal",
        "authority": doc["authority"],
        "document_type": doc["document_type"],
        "source_url": downloaded_from,
        "version": doc["version"],
        "publication_date": doc["publication_date"],
        "effective_from": None,
        "effective_to": None,
        "document_status": doc["status"],
        "sha256": sha256_hash,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    })

manifest_path = TARGET_DIR / "download_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"\nDownloaded and PDF-validated {len(manifest)}/{len(DOCUMENTS)} official documents to: {TARGET_DIR}")
print(f"SHA-256 manifest: {manifest_path}")
