#!/usr/bin/env python3
"""Cross-platform script to upload Indian legal documents and G Inc demo policies to the running API."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")
REPO_ROOT = Path(__file__).resolve().parent.parent


def check_health():
    url = f"{API_BASE}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            if data.get("status") not in {"ok", "degraded"}:
                print(f"Warning: Health status is {data.get('status')}")
            return True
    except Exception as e:
        print(f"Error: API health check failed at {url}: {e}", file=sys.stderr)
        return False


def get_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def post_multipart(url, fields, file_field_name, file_path, content_type):
    boundary = "----WebKitFormBoundary" + os.urandom(16).hex()
    body = bytearray()

    for k, v in fields.items():
        if v is not None:
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))

    file_bytes = file_path.read_bytes()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_path.name}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def upload_legal_corpus():
    manifest_path = REPO_ROOT / "data" / "legal" / "india" / "dpdp" / "download_manifest.json"
    if not manifest_path.exists():
        print(f"Notice: download_manifest.json not found at {manifest_path}. Run download_indian_demo_docs.py first if you want legal docs.")
        return

    registered = {d["filename"] for d in get_json(f"{API_BASE}/api/v1/documents")}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for doc in manifest:
        filename = doc["filename"]
        file_path = REPO_ROOT / "data" / "legal" / "india" / "dpdp" / filename
        if not file_path.exists():
            print(f"Skipping missing file: {filename}")
            continue
        if filename in registered:
            print(f"Already registered legal doc: {filename}")
            continue

        print(f"Uploading legal document: {doc['title']}...")
        fields = {
            "title": doc.get("title"),
            "jurisdiction": doc.get("jurisdiction"),
            "country": doc.get("country"),
            "domain": doc.get("domain"),
            "authority": doc.get("authority"),
            "document_type": doc.get("document_type"),
            "source_url": doc.get("source_url"),
            "version": doc.get("version"),
            "publication_date": doc.get("publication_date"),
            "document_status": doc.get("document_status", "unknown"),
        }
        try:
            post_multipart(f"{API_BASE}/api/v1/documents/upload", fields, "file", file_path, "application/pdf")
            print(f"Successfully uploaded: {filename}")
        except Exception as e:
            print(f"Failed to upload {filename}: {e}", file=sys.stderr)


def upload_company_policies():
    policy_dir = REPO_ROOT / "data" / "company" / "g-inc"
    if not policy_dir.exists():
        print(f"Notice: Policy directory {policy_dir} does not exist.")
        return

    try:
        registered = {d["filename"] for d in get_json(f"{API_BASE}/api/v1/company/documents")}
    except Exception as e:
        print(f"Could not list company documents: {e}", file=sys.stderr)
        return

    policies = sorted(p for p in policy_dir.glob("*.md") if p.name.lower() != "readme.md")
    if not policies:
        print(f"No company policy markdown files found in {policy_dir}")
        return

    for policy in policies:
        if policy.name in registered:
            print(f"Already registered policy: {policy.name}")
            continue

        print(f"Uploading company policy: {policy.name}...")
        fields = {"title": policy.stem}
        try:
            post_multipart(f"{API_BASE}/api/v1/company/documents/upload", fields, "file", policy, "text/markdown")
            print(f"Successfully uploaded: {policy.name}")
        except Exception as e:
            print(f"Failed to upload {policy.name}: {e}", file=sys.stderr)


def main():
    if not check_health():
        print(f"API is not running at {API_BASE}. Please start the backend service first.", file=sys.stderr)
        sys.exit(1)

    print("Uploading legal corpus...")
    upload_legal_corpus()
    print("\nUploading G Inc demo policies...")
    upload_company_policies()
    print("\nUpload complete.")


if __name__ == "__main__":
    main()
