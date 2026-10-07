import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase


BACKEND_DIR = Path(__file__).resolve().parents[2]
GRAPH_DIR = BACKEND_DIR.parent / "graph"

load_dotenv(GRAPH_DIR / ".env", override=True)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def write_analysis_to_neo4j(
    campaign_id: str,
    campaign_name: str,
    scam_type: str,
    incident_id: str,
    risk_score: int,
    risk_level: str,
    entities: list[Any],
) -> bool:

    if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
        raise RuntimeError("Neo4j configuration is missing")

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )

    try:
        with driver.session() as session:
            session.execute_write(
                _write_transaction,
                campaign_id,
                campaign_name,
                scam_type,
                incident_id,
                risk_score,
                risk_level,
                entities,
            )
        return True
    finally:
        driver.close()


def _get_entity_field(entity: Any, *names: str):
    """Support Pydantic models, dictionaries, and normal objects."""
    for name in names:
        if isinstance(entity, dict):
            value = entity.get(name)
        else:
            value = getattr(entity, name, None)

        if value is not None:
            return value

    return None


def _write_transaction(
    tx,
    campaign_id: str,
    campaign_name: str,
    scam_type: str,
    incident_id: str,
    risk_score: int,
    risk_level: str,
    entities: list[Any],
) -> None:

    # Campaign
    tx.run(
        """
        MERGE (c:Campaign {id: $campaign_id})
        SET
            c.name = $campaign_name,
            c.scam_type = $scam_type,
            c.risk_score = $risk_score,
            c.risk_level = $risk_level
        """,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        scam_type=scam_type,
        risk_score=int(risk_score),
        risk_level=risk_level,
    )

    # Incident
    tx.run(
        """
        MERGE (i:Incident {id: $incident_id})
        SET
            i.severity = $risk_level,
            i.risk_score = $risk_score,
            i.scam_type = $scam_type
        WITH i
        MATCH (c:Campaign {id: $campaign_id})
        MERGE (i)-[:PART_OF]->(c)
        """,
        incident_id=incident_id,
        campaign_id=campaign_id,
        risk_score=int(risk_score),
        risk_level=risk_level,
        scam_type=scam_type,
    )

    # Entities
    for entity in entities or []:

        entity_id = _get_entity_field(
            entity,
            "entity_id",
            "id",
        )

        entity_type = _get_entity_field(
            entity,
            "entity_type",
            "type",
        )

        value = _get_entity_field(
            entity,
            "value",
            "url",
            "phone",
            "upi_id",
        )

        if not value:
            continue

        entity_type = str(entity_type or "ENTITY").upper()
        value = str(value)

        if not entity_id:
            safe_value = (
                value.replace("https://", "")
                .replace("http://", "")
                .replace("/", "_")
                .replace("@", "_")
                .replace(".", "_")
            )
            entity_id = f"{entity_type}_{safe_value}"

        entity_id = str(entity_id)

        # URL
        if entity_type == "URL":

            tx.run(
                """
                MERGE (u:URL {id: $entity_id})
                SET u.url = $value
                WITH u
                MATCH (i:Incident {id: $incident_id})
                MERGE (i)-[:USES]->(u)
                """,
                entity_id=entity_id,
                value=value,
                incident_id=incident_id,
            )

        # Phone
        elif entity_type in {"PHONE", "PHONE_NUMBER", "MOBILE"}:

            tx.run(
                """
                MERGE (p:Phone {id: $entity_id})
                SET p.phone = $value
                WITH p
                MATCH (i:Incident {id: $incident_id})
                MERGE (i)-[:INVOLVES]->(p)
                """,
                entity_id=entity_id,
                value=value,
                incident_id=incident_id,
            )

        # UPI
        elif entity_type in {"UPI", "UPI_ID"}:

            tx.run(
                """
                MERGE (u:UPI {id: $entity_id})
                SET u.value = $value
                WITH u
                MATCH (i:Incident {id: $incident_id})
                MERGE (i)-[:INVOLVES]->(u)
                """,
                entity_id=entity_id,
                value=value,
                incident_id=incident_id,
            )

        # Account
        elif entity_type in {"ACCOUNT", "BANK_ACCOUNT"}:

            tx.run(
                """
                MERGE (a:Account {id: $entity_id})
                SET a.value = $value
                WITH a
                MATCH (i:Incident {id: $incident_id})
                MERGE (i)-[:INVOLVES]->(a)
                """,
                entity_id=entity_id,
                value=value,
                incident_id=incident_id,
            )

        # Other entity
        else:

            tx.run(
                """
                MERGE (e:Entity {id: $entity_id})
                SET
                    e.type = $entity_type,
                    e.value = $value
                WITH e
                MATCH (i:Incident {id: $incident_id})
                MERGE (i)-[:INVOLVES]->(e)
                """,
                entity_id=entity_id,
                entity_type=entity_type,
                value=value,
                incident_id=incident_id,
            )