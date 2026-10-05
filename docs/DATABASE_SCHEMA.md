MULEX Database Schema

MULEX uses:

- PostgreSQL for application data
- Neo4j for fraud/network relationships

---

PostgreSQL

reports

Stores citizen-submitted reports.

Field| Type| Description
id| UUID| Internal primary key
report_id| String| Public report ID
description| Text| User report
phone| String| Optional
upi_id| String| Optional
url| String| Optional
created_at| Timestamp| Submission time

---

incidents

Represents a normalized fraud incident.

Field| Type| Description
id| UUID| Internal primary key
incident_id| String| Public ID
risk_score| Integer| 0–100
risk_level| String| LOW/MEDIUM/HIGH/CRITICAL
scam_type| String| Scam category
confidence| Float| AI confidence
created_at| Timestamp| Creation time

---

entities

Stores extracted entities.

Field| Type| Description
id| UUID| Internal primary key
entity_id| String| Public ID
type| String| PHONE/UPI/URL/etc
value| String| Entity value

---

incident_entities

Many-to-many relationship between incidents and entities.

Field| Type
incident_id| UUID
entity_id| UUID

---

campaigns

Represents a suspected coordinated fraud campaign.

Field| Type| Description
id| UUID| Internal primary key
campaign_id| String| Public ID
name| String| Campaign name
risk_score| Integer| 0–100
scam_type| String| Main scam category
created_at| Timestamp| Creation time

---

incident_campaigns

Links incidents to campaigns.

Field| Type
incident_id| UUID
campaign_id| UUID

---

transactions

Synthetic transaction data for the prototype.

Field| Type
id| UUID
transaction_id| String
sender_account| String
receiver_account| String
amount| Decimal
timestamp| Timestamp

---

Neo4j

Neo4j represents relationships.

Node Types

Victim
Account
Mule
Transaction
Phone
UPI
URL
Incident
Campaign
Beneficiary

---

Relationships

Possible relationships:

(:Victim)-[:REPORTED]->(:Incident)

(:Incident)-[:INVOLVES]->(:Phone)

(:Incident)-[:INVOLVES]->(:UPI)

(:Incident)-[:PART_OF]->(:Campaign)

(:Victim)-[:TRANSFERRED]->(:Account)

(:Account)-[:TRANSFERRED_TO]->(:Account)

(:Account)-[:LINKED_TO]->(:Campaign)

---

Important Rule

PostgreSQL is the primary application database.

Neo4j is used for relationship and network analysis.

Do not duplicate unrelated application data between the two databases.

The backend is the gateway between the frontend and databases.