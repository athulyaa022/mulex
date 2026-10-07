import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

from mule_detector import calculate_mule_risk


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)


# ---------------------------------------------------------
# NEO4J CONNECTION
# ---------------------------------------------------------

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


# ---------------------------------------------------------
# GET ACCOUNT NETWORK
# ---------------------------------------------------------

def get_account_network(account_id):

    with driver.session() as session:

        result = session.run(
            """
            MATCH (a:Account {id: $account_id})

            OPTIONAL MATCH path =
                (a)-[:SENT|RECEIVED_BY|USES]-(connected)

            RETURN
                a,
                connected,
                relationships(path) AS rels
            """,
            account_id=account_id
        )

        nodes = {}
        edges = {}

        for record in result:

            account = record["a"]
            connected = record["connected"]
            relationships = record["rels"]

            # -------------------------------------------------
            # Add main account
            # -------------------------------------------------

            if account is not None:

                account_id_value = account["id"]

                nodes[account_id_value] = {
                    "id": account_id_value,
                    "label": "Account",
                    "properties": dict(account)
                }

            # -------------------------------------------------
            # Add connected node
            # -------------------------------------------------

            if connected is not None:

                connected_id = connected.element_id

                labels = list(connected.labels)

                if labels:
                    label = labels[0]
                else:
                    label = "Node"

                if "id" in connected:
                    node_id = connected["id"]
                else:
                    node_id = connected_id

                nodes[node_id] = {
                    "id": node_id,
                    "label": label,
                    "properties": dict(connected)
                }

            # -------------------------------------------------
            # Add relationships
            # -------------------------------------------------

            if relationships:

                for relationship in relationships:

                    start_node = relationship.start_node
                    end_node = relationship.end_node

                    if "id" in start_node:
                        start_id = start_node["id"]
                    else:
                        start_id = start_node.element_id

                    if "id" in end_node:
                        end_id = end_node["id"]
                    else:
                        end_id = end_node.element_id

                    edge_id = relationship.element_id

                    edges[edge_id] = {
                        "id": edge_id,
                        "source": start_id,
                        "target": end_id,
                        "type": relationship.type
                    }

        # -----------------------------------------------------
        # CALCULATE MULE RISK
        # -----------------------------------------------------

        risk_result = calculate_mule_risk(account_id)

        # -----------------------------------------------------
        # FINAL RESPONSE
        # -----------------------------------------------------

        return {
            "account_id": account_id,

            "nodes": list(nodes.values()),

            "edges": list(edges.values()),

            "risk_score": risk_result["risk_score"],

            "risk_level": risk_result["risk_level"],

            "evidence": risk_result["evidence"],

            "statistics": {
                "incoming_transactions":
                    risk_result["incoming_transactions"],

                "outgoing_transactions":
                    risk_result["outgoing_transactions"],

                "unique_senders":
                    risk_result["unique_senders"],

                "unique_receivers":
                    risk_result["unique_receivers"],

                "incoming_amount":
                    risk_result["incoming_amount"],

                "outgoing_amount":
                    risk_result["outgoing_amount"],

                "rapid_activity":
                    risk_result["rapid_activity"],

                "rapid_matches":
                    risk_result["rapid_matches"],

                "fastest_pass_through_minutes":
                    risk_result["fastest_pass_through"]
            }
        }
def get_campaign_network(campaign_id):
    """Return a connected Neo4j network for a fraud campaign."""

    with driver.session() as session:

        result = session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})

            OPTIONAL MATCH (i:Incident)-[:PART_OF]->(c)

            OPTIONAL MATCH (i)-[r1:INVOLVES|USES]-(connected)

            RETURN
                c,
                i,
                connected,
                collect(DISTINCT r1) AS relationships
            """,
            campaign_id=campaign_id,
        )

        records = list(result)

        if not records:
            return None

        nodes = {}
        edges = {}

        for record in records:

            campaign = record["c"]
            incident = record["i"]
            connected = record["connected"]
            relationships = record["relationships"]

            # Campaign node
            if campaign is not None:
                campaign_node_id = campaign["id"]

                nodes[campaign_node_id] = {
                    "id": campaign_node_id,
                    "type": "CAMPAIGN",
                    "label": campaign.get("name", campaign_node_id),
                }

            # Incident node
            if incident is not None:
                incident_id = incident.get("id")

                if incident_id:
                    nodes[incident_id] = {
                        "id": incident_id,
                        "type": "INCIDENT",
                        "label": incident.get("severity", "Incident"),
                    }

            # Connected node
            if connected is not None:

                if "id" in connected:
                    node_id = connected["id"]
                else:
                    node_id = connected.element_id

                labels = list(connected.labels)

                node_type = labels[0].upper() if labels else "NODE"

                nodes[node_id] = {
                    "id": node_id,
                    "type": node_type,
                    "label": str(
                        connected.get("name")
                        or connected.get("id")
                        or node_type
                    ),
                }

            # Relationships
            for relationship in relationships:

                if relationship is None:
                    continue

                start_node = relationship.start_node
                end_node = relationship.end_node

                start_id = (
                    start_node["id"]
                    if "id" in start_node
                    else start_node.element_id
                )

                end_id = (
                    end_node["id"]
                    if "id" in end_node
                    else end_node.element_id
                )

                edges[relationship.element_id] = {
                    "id": relationship.element_id,
                    "source": start_id,
                    "target": end_id,
                    "type": relationship.type,
                }

        intelligence = None

        try:
            from graph_queries import get_campaign_intelligence

            intelligence = get_campaign_intelligence(campaign_id)
        except Exception:
            intelligence = None

        if intelligence and "error" not in intelligence:

            risk_score = intelligence.get("risk_score", 0)
            risk_level = intelligence.get("risk_level", "LOW")

            evidence = [
                f"{intelligence.get('incident_count', 0)} incidents",
                f"{intelligence.get('account_count', 0)} connected accounts",
                f"{intelligence.get('url_count', 0)} connected URLs",
                f"{intelligence.get('phone_count', 0)} connected phones",
                f"{intelligence.get('upi_count', 0)} connected UPI IDs",
            ]

            statistics = {
                "connected_accounts": intelligence.get(
                    "account_count", 0
                ),
            }

        else:
            risk_score = 0
            risk_level = "LOW"
            evidence = []
            statistics = {}

        return {
            "campaign_id": campaign_id,
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "evidence": evidence,
            "statistics": statistics,
            "intelligence_summary": intelligence,
        }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print()
    print("========================================")
    print("MULEX GRAPH SERVICE")
    print("========================================")

    account_id = "ACC0905"

    result = get_account_network(account_id)

    print()
    print("Account:", result["account_id"])

    print(
        "Risk Score:",
        result["risk_score"],
        "/100"
    )

    print(
        "Risk Level:",
        result["risk_level"]
    )

    print()
    print(
        "Nodes:",
        len(result["nodes"])
    )

    print(
        "Edges:",
        len(result["edges"])
    )

    print()
    print("Statistics")
    print("----------")

    stats = result["statistics"]

    print(
        "Incoming transactions:",
        stats["incoming_transactions"]
    )

    print(
        "Outgoing transactions:",
        stats["outgoing_transactions"]
    )

    print(
        "Unique senders:",
        stats["unique_senders"]
    )

    print(
        "Unique receivers:",
        stats["unique_receivers"]
    )

    print(
        "Incoming amount:",
        stats["incoming_amount"]
    )

    print(
        "Outgoing amount:",
        stats["outgoing_amount"]
    )

    print(
        "Rapid activity:",
        stats["rapid_activity"]
    )

    print(
        "Rapid pairs:",
        stats["rapid_matches"]
    )

    print(
        "Fastest pass-through:",
        stats["fastest_pass_through_minutes"],
        "minutes"
    )

    print()
    print("Evidence")
    print("--------")

    for evidence in result["evidence"]:
        print("-", evidence)

    print()
    print("========================================")
    print("GRAPH SERVICE TEST COMPLETE")
    print("========================================")


# ---------------------------------------------------------
# CLOSE DRIVER
# ---------------------------------------------------------

