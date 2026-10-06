from mule_detector import calculate_mule_risk
from neo4j_connection import get_driver


# ---------------------------------------------------------
# GET ACCOUNT NETWORK
# ---------------------------------------------------------

def get_account_network(account_id):

    with get_driver().session() as session:

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


def get_campaign_network(campaign_id: str) -> dict | None:
    from graph_queries import get_campaign_intelligence

    intelligence = get_campaign_intelligence(campaign_id)
    if intelligence is None:
        return None

    with get_driver().session() as session:
        records = session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            OPTIONAL MATCH (i:Incident)-[:PART_OF]->(c)
            OPTIONAL MATCH (i)-[incident_rel:INVOLVES|USES]->(entity)
            RETURN c, i, incident_rel, entity
            """,
            campaign_id=campaign_id,
        )
        nodes: dict[str, dict] = {}
        edges: dict[tuple[str, str, str], dict] = {}
        incident_ids: set[str] = set()
        for record in records:
            campaign = record["c"]
            _add_node(nodes, campaign, "CAMPAIGN")
            incident = record["i"]
            entity = record["entity"]
            relationship = record["incident_rel"]
            if incident is not None:
                incident_id = incident.get("id", incident.element_id)
                incident_ids.add(incident_id)
                _add_node(nodes, incident, "INCIDENT")
                edges[(incident_id, campaign["id"], "PART_OF")] = {
                    "source": incident_id, "target": campaign["id"], "type": "PART_OF"
                }
            if entity is not None and incident is not None:
                _add_node(nodes, entity, None)
                entity_id = entity.get("id", entity.element_id)
                edges[(incident_id, entity_id, relationship.type)] = {
                    "source": incident_id,
                    "target": entity_id,
                    "type": relationship.type,
                }

    accounts = [node["id"] for node in nodes.values() if node["type"] == "Account"]
    account_risks = []
    statistics = {
        "incoming_transactions": 0,
        "outgoing_transactions": 0,
        "unique_senders": 0,
        "unique_receivers": 0,
        "incoming_amount": 0.0,
        "outgoing_amount": 0.0,
        "rapid_activity": False,
        "rapid_matches": 0,
        "fastest_pass_through_minutes": None,
    }
    evidence = [f"{intelligence['incident_count']} incident(s) linked to this graph campaign."]
    for account_id in accounts[:20]:
        risk = calculate_mule_risk(account_id)
        if risk is None:
            continue
        account_risks.append(risk["risk_score"])
        for key in (
            "incoming_transactions", "outgoing_transactions", "unique_senders",
            "unique_receivers", "rapid_matches",
        ):
            statistics[key] += risk[key]
        for key in ("incoming_amount", "outgoing_amount"):
            statistics[key] += float(risk[key])
        statistics["rapid_activity"] |= bool(risk["rapid_activity"])
        fastest = risk["fastest_pass_through"]
        if fastest is not None and (
            statistics["fastest_pass_through_minutes"] is None
            or fastest < statistics["fastest_pass_through_minutes"]
        ):
            statistics["fastest_pass_through_minutes"] = fastest
        evidence.extend(risk["evidence"])

    evidence = list(dict.fromkeys(evidence))
    return {
        "graph_campaign_id": campaign_id,
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "risk_score": max([intelligence["risk_score"], *account_risks]),
        "risk_level": "HIGH" if max([intelligence["risk_score"], *account_risks]) >= 70 else intelligence["risk_level"],
        "evidence": evidence,
        "statistics": statistics,
        "intelligence_summary": intelligence,
    }


def _add_node(nodes: dict[str, dict], node, fallback_label: str | None) -> None:
    labels = list(node.labels)
    node_type = labels[0] if labels else (fallback_label or "Node")
    node_id = node.get("id", node.element_id)
    nodes[node_id] = {
        "id": node_id,
        "type": node_type,
        "label": node.get("name") or node.get("value") or node_type,
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
