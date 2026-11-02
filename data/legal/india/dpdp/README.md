# India DPDP demo corpus

This directory is the target for `scripts/download_indian_demo_docs.ps1`. Run that script from any working directory in PowerShell on a machine with access to the official sites. It downloads four primary documents, checks that each response is a PDF, and writes `download_manifest.json` containing source URLs and SHA-256 hashes.

The corpus covers the **Digital Personal Data Protection Act, 2023** and its 2025 Rules and commencement instruments. It is a focused demo corpus, not all Indian privacy or compliance law and not a legal research collection complete enough for real compliance decisions.

The Rules were published with phased commencement and have a corrigendum. The downloader preserves the original Rules and corrigendum as separate records so the original Gazette text is not silently altered. Use the Rules together with the corrigendum and the applicable commencement notification. The download manifest leaves effective dates unset because applicability differs by provision.

Official sources:

- [DPDP Act, 2023 — India Code](https://www.indiacode.nic.in/bitstream/123456789/22037/2/a2023-22.pdf)
- [DPDP Rules, 2025, G.S.R. 846(E) — Official Gazette](https://egazette.gov.in/WriteReadData/2025/267650.pdf)
- [DPDP Act commencement notification, G.S.R. 843(E) — Official Gazette](https://egazette.gov.in/WriteReadData/2025/267647.pdf)
- [DPDP Rules corrigendum, G.S.R. 892(E) — MeitY](https://www.meity.gov.in/static/uploads/2025/12/3c7ebbae0e5456f493f486e6845df86b.pdf)

Only these government PDFs belong in the legal knowledge base. The synthetic G Inc drafts under `data/company/g-inc/` are company documents and must never be presented as legal authority.
