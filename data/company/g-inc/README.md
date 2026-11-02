# G Inc demo company documents

**G Inc is fictional.** Every document in this folder is a synthetic draft created only for a software demonstration. It does not describe a real company, make a legal-compliance determination, or establish production policy. The time periods and operational targets in these examples are invented internal choices for the demo, not statutory deadlines or legal requirements.

Keep these files separate from `data/legal/`. The local prototype now has a separate, single-company G Inc demo collection and a Company Review page. The demo has no authentication or multi-tenant authorization, is disabled when `APP_ENV=production`, and must not be exposed to a network or used for confidential documents. Use the Company Review upload control; do not send these drafts to the legal document endpoint, which classifies uploads as legal material. Generated comparison requires `OPENAI_API_KEY`; without it, the API only retrieves and displays both evidence sets.

Sample company: G Inc, a fictional India-based software services company with employees and business customers.

Drafts:

- `G-Inc-Employee-and-Customer-Privacy-Policy-DRAFT.md`
- `G-Inc-Data-Retention-and-Deletion-Standard-DRAFT.md`
- `G-Inc-Personal-Data-Incident-Response-Procedure-DRAFT.md`
- `G-Inc-Vendor-and-Processor-Management-Standard-DRAFT.md`
- `G-Inc-Access-Control-and-Security-Standard-DRAFT.md`

Each should be reviewed and adapted by qualified counsel and company owners before any real-world use. For demo compliance comparisons, provide the fictional policies as the company-evidence set and the official PDFs as the legal-evidence set.
