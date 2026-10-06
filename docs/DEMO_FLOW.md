MULEX Hackathon Demo Flow

Objective

Demonstrate that MULEX can move from an individual suspicious message to a larger coordinated fraud campaign and financial network.

---

Demo Scenario

A citizen receives an AI-generated KYC scam message.

Example:

«Your bank account will be suspended today. Complete KYC verification immediately using the following link.»

---

Step 1 — Citizen Check

User enters the suspicious message into MULEX.

Frontend sends:

POST /api/v1/analyze

---

Step 2 — AI Analysis

MULEX identifies:

- KYC impersonation
- urgency
- suspicious link
- financial manipulation
- possible AI-generated content

Result:

HIGH RISK

Example:

Risk Score: 87/100

---

Step 3 — Entity Extraction

MULEX extracts:

- phone number
- URL
- UPI ID
- bank identity

---

Step 4 — Cross-Incident Correlation

MULEX searches previous incidents.

It discovers that the same URL/UPI/phone appears in multiple reports.

Example:

17 related incidents

---

Step 5 — Campaign Detection

The incidents are grouped into:

CMP-001

"KYC Impersonation Campaign"

Campaign risk:

94/100

---

Step 6 — Network View

MULEX displays:

Victims
↓
Mule Accounts
↓
Layering Accounts
↓
Final Beneficiary

The graph highlights suspicious accounts and relationships.

---

Step 7 — Explainability

Show why the network was flagged.

Example:

- 17 related incidents
- 6 shared identifiers
- multiple incoming accounts
- rapid outgoing transfers
- repeated fraud pattern

---

Final Message

MULEX does not simply identify a suspicious message.

It connects fragmented fraud signals to reveal the larger campaign and network behind the fraud.

---

Demo Data

Use synthetic data only.

No real bank accounts or private financial information.

---

Demo Rules

The demo must work offline or with a reliable fallback wherever possible.

Use deterministic demo data.

Do not depend entirely on a live external AI API.

If an external AI service fails, the demo must still produce a valid result using fallback/mock intelligence.

---

Target Demo Duration

3–4 minutes.