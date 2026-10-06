import os
import json

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


# ============================================================
# CONNECT TO NEO4J
# ============================================================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


# ============================================================
# LOAD GENERATED DATA
# ============================================================

data_file = os.path.join(
    os.path.dirname(__file__),
    "data",
    "mulex_data.json"
)

with open(data_file, "r", encoding="utf-8") as file:
    data = json.load(file)


# ============================================================
# SEED DATABASE
# ============================================================

def seed_database():

    with driver.session() as session:

        # ----------------------------------------------------
        # CLEAR OLD GRAPH
        # ----------------------------------------------------

        print("Clearing old MULEX graph...")

        session.run(
            """
            MATCH (n)
            DETACH DELETE n
            """
        )


        # ----------------------------------------------------
        # CREATE ACCOUNTS
        # ----------------------------------------------------

        print("Creating accounts...")

        session.run(
            """
            UNWIND $accounts AS account

            MERGE (a:Account {id: account.id})

            SET a.type = account.type
            """,
            accounts=data["accounts"]
        )


        # ----------------------------------------------------
        # CREATE PHONES
        # ----------------------------------------------------

        print("Creating phones...")

        session.run(
            """
            UNWIND $phones AS phone

            MERGE (p:Phone {id: phone.id})

            SET p.number = phone.number
            """,
            phones=data["phones"]
        )


        # ----------------------------------------------------
        # CREATE UPI IDS
        # ----------------------------------------------------

        print("Creating UPI IDs...")

        session.run(
            """
            UNWIND $upi_ids AS upi

            MERGE (u:UPI {id: upi.id})

            SET u.value = upi.value
            """,
            upi_ids=data["upi_ids"]
        )


        # ----------------------------------------------------
        # CREATE URLS
        # ----------------------------------------------------

        print("Creating URLs...")

        session.run(
            """
            UNWIND $urls AS url

            MERGE (u:URL {id: url.id})

            SET u.value = url.value
            """,
            urls=data["urls"]
        )


        # ----------------------------------------------------
        # CREATE CAMPAIGNS
        # ----------------------------------------------------

        print("Creating campaigns...")

        session.run(
            """
            UNWIND $campaigns AS campaign

            MERGE (c:Campaign {id: campaign.id})

            SET c.name = campaign.name,
                c.scam_type = campaign.scam_type
            """,
            campaigns=data["campaigns"]
        )


        # ----------------------------------------------------
        # CREATE INCIDENTS
        # ----------------------------------------------------

        print("Creating incidents...")

        session.run(
            """
            UNWIND $incidents AS incident

            MERGE (i:Incident {id: incident.id})

            SET i.scam_type = incident.scam_type,
                i.severity = incident.severity,
                i.reported_date = incident.reported_date
            """,
            incidents=data["incidents"]
        )


        # ----------------------------------------------------
        # LINK INCIDENTS TO CAMPAIGNS
        # ----------------------------------------------------

        print("Linking incidents to campaigns...")

        session.run(
            """
            UNWIND $incidents AS incident

            MATCH (i:Incident {id: incident.id})

            MATCH (c:Campaign {id: incident.campaign_id})

            MERGE (i)-[:PART_OF]->(c)
            """,
            incidents=data["incidents"]
        )


        # ----------------------------------------------------
        # CREATE TRANSACTIONS
        # ----------------------------------------------------

        print("Creating transactions...")

        session.run(
            """
            UNWIND $transactions AS transaction

            MERGE (t:Transaction {id: transaction.id})

            SET t.amount = transaction.amount,
                t.date = transaction.date
            """,
            transactions=data["transactions"]
        )


        # ----------------------------------------------------
        # LINK TRANSACTIONS
        # Account → Transaction → Account
        # ----------------------------------------------------

        print("Linking transactions...")

        session.run(
            """
            UNWIND $transactions AS transaction

            MATCH (sender:Account {
                id: transaction.sender
            })

            MATCH (receiver:Account {
                id: transaction.receiver
            })

            MATCH (t:Transaction {
                id: transaction.id
            })

            MERGE (sender)-[:SENT]->(t)

            MERGE (t)-[:RECEIVED_BY]->(receiver)
            """,
            transactions=data["transactions"]
        )


        # ====================================================
        # NEW CONNECTIONS
        # ====================================================


        # ----------------------------------------------------
        # ACCOUNT → PHONE
        # ACCOUNT → UPI
        # ----------------------------------------------------

        print("Linking accounts to phones and UPI IDs...")

        account_links = []

        for index, account in enumerate(data["accounts"]):

            phone_number = (index % 100) + 1
            upi_number = (index % 100) + 1

            account_links.append({
                "account_id": account["id"],
                "phone_id": f"PHONE{phone_number:03d}",
                "upi_id": f"UPI{upi_number:03d}"
            })


        session.run(
            """
            UNWIND $links AS link

            MATCH (a:Account {
                id: link.account_id
            })

            MATCH (p:Phone {
                id: link.phone_id
            })

            MATCH (u:UPI {
                id: link.upi_id
            })

            MERGE (a)-[:USES]->(p)

            MERGE (a)-[:USES]->(u)
            """,
            links=account_links
        )


        # ----------------------------------------------------
        # INCIDENT → ACCOUNT
        # INCIDENT → URL
        # ----------------------------------------------------

        print("Linking incidents to accounts and URLs...")

        incident_links = []

        for index, incident in enumerate(data["incidents"]):

            account_number = (index % 1000) + 1
            url_number = (index % 50) + 1

            incident_links.append({
                "incident_id": incident["id"],
                "account_id": f"ACC{account_number:04d}",
                "url_id": f"URL{url_number:03d}"
            })


        session.run(
            """
            UNWIND $links AS link

            MATCH (i:Incident {
                id: link.incident_id
            })

            MATCH (a:Account {
                id: link.account_id
            })

            MATCH (u:URL {
                id: link.url_id
            })

            MERGE (i)-[:INVOLVES]->(a)

            MERGE (i)-[:USES]->(u)
            """,
            links=incident_links
        )


        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        print("Additional graph connections created.")

        print("")
        print("================================")
        print("MULEX DATABASE SEEDED SUCCESSFULLY")
        print("================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:
        seed_database()

    finally:
        driver.close()