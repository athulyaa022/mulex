import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load .env from the graph folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)


# Neo4j connection details
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


# Create Neo4j driver
driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


def get_campaign_intelligence(campaign_id):
    """
    Analyze a fraud campaign and find:
    - Number of incidents
    - Connected accounts
    - Connected URLs
    - Connected phones
    - Connected UPI IDs
    - Incident severity
    """

    with driver.session() as session:

        # -------------------------------------------------
        # 1. Get campaign information
        # -------------------------------------------------

        campaign_result = session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            RETURN
                c.id AS campaign_id,
                c.name AS campaign_name,
                c.scam_type AS scam_type
            """,
            campaign_id=campaign_id
        )

        campaign = campaign_result.single()

        if campaign is None:
            return {
                "error": f"Campaign {campaign_id} not found"
            }


        # -------------------------------------------------
        # 2. Count incidents
        # -------------------------------------------------

        incident_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            RETURN count(DISTINCT i) AS incident_count
            """,
            campaign_id=campaign_id
        )

        incident_count = incident_result.single()["incident_count"]


        # -------------------------------------------------
        # 3. Count connected accounts
        # -------------------------------------------------

        account_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            MATCH (i)-[:INVOLVES]->(a:Account)
            RETURN count(DISTINCT a) AS account_count
            """,
            campaign_id=campaign_id
        )

        account_count = account_result.single()["account_count"]


        # -------------------------------------------------
        # 4. Count connected URLs
        # -------------------------------------------------

        url_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            MATCH (i)-[:USES]->(u:URL)
            RETURN count(DISTINCT u) AS url_count
            """,
            campaign_id=campaign_id
        )

        url_count = url_result.single()["url_count"]


        # -------------------------------------------------
        # 5. Count connected phone numbers
        # -------------------------------------------------

        phone_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            MATCH (i)-[:INVOLVES]->(a:Account)
            MATCH (a)-[:USES]->(p:Phone)
            RETURN count(DISTINCT p) AS phone_count
            """,
            campaign_id=campaign_id
        )

        phone_count = phone_result.single()["phone_count"]


        # -------------------------------------------------
        # 6. Count connected UPI IDs
        # -------------------------------------------------

        upi_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            MATCH (i)-[:INVOLVES]->(a:Account)
            MATCH (a)-[:USES]->(u:UPI)
            RETURN count(DISTINCT u) AS upi_count
            """,
            campaign_id=campaign_id
        )

        upi_count = upi_result.single()["upi_count"]


        # -------------------------------------------------
        # 7. Get incident severity distribution
        # -------------------------------------------------

        severity_result = session.run(
            """
            MATCH (i:Incident)-[:PART_OF]->(c:Campaign {id: $campaign_id})
            RETURN
                i.severity AS severity,
                count(i) AS count
            ORDER BY count DESC
            """,
            campaign_id=campaign_id
        )

        severity_breakdown = {}

        for record in severity_result:
            severity = record["severity"]

            if severity is None:
                severity = "UNKNOWN"

            severity_breakdown[severity] = record["count"]


        # -------------------------------------------------
        # 8. Calculate campaign risk score
        # -------------------------------------------------

        risk_score = 0

        if incident_count >= 10:
            risk_score += 30
        elif incident_count >= 5:
            risk_score += 20
        elif incident_count >= 2:
            risk_score += 10


        if account_count >= 10:
            risk_score += 25
        elif account_count >= 5:
            risk_score += 15


        if url_count >= 3:
            risk_score += 15
        elif url_count >= 1:
            risk_score += 5


        if phone_count >= 5:
            risk_score += 15
        elif phone_count >= 2:
            risk_score += 5


        if upi_count >= 5:
            risk_score += 15
        elif upi_count >= 2:
            risk_score += 5


        # Limit score to 100
        risk_score = min(risk_score, 100)


        # Determine risk level
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"


        # -------------------------------------------------
        # 9. Return complete campaign intelligence
        # -------------------------------------------------

        return {
            "campaign_id": campaign["campaign_id"],
            "campaign_name": campaign["campaign_name"],
            "scam_type": campaign["scam_type"],
            "incident_count": incident_count,
            "account_count": account_count,
            "url_count": url_count,
            "phone_count": phone_count,
            "upi_count": upi_count,
            "severity_breakdown": severity_breakdown,
            "risk_score": risk_score,
            "risk_level": risk_level
        }

def resolve_campaign_id(campaign_id, entity_values=None):
    """
    Resolve a MULEX campaign to a campaign existing in Neo4j.

    First tries an exact campaign ID.
    Then tries matching extracted entity values against graph nodes.
    """

    entity_values = entity_values or []

    with driver.session() as session:

        # -------------------------------------------------
        # 1. Exact campaign ID
        # -------------------------------------------------

        result = session.run(
            """
            MATCH (c:Campaign {id: $campaign_id})
            RETURN c.id AS campaign_id
            """,
            campaign_id=campaign_id,
        )

        record = result.single()

        if record:
            return record["campaign_id"]

        # -------------------------------------------------
        # 2. Match an extracted entity
        # -------------------------------------------------

        if entity_values:

            result = session.run(
                """
                MATCH (c:Campaign)<-[:PART_OF]-(i:Incident)
                MATCH (i)-[]-(n)

                WHERE
                    any(
                        value IN $entity_values
                        WHERE
                            toString(n.id) = value
                            OR toString(n.value) = value
                            OR toString(n.url) = value
                            OR toString(n.phone) = value
                    )

                RETURN c.id AS campaign_id
                LIMIT 1
                """,
                entity_values=entity_values,
            )

            record = result.single()

            if record:
                return record["campaign_id"]

    return None

# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print()
    print("========================================")
    print("MULEX CAMPAIGN INTELLIGENCE")
    print("========================================")

    campaign_id = "CAMP007"

    result = get_campaign_intelligence(campaign_id)

    if "error" in result:

        print(result["error"])

    else:

        print()
        print("Campaign:", result["campaign_id"])
        print("Name:", result["campaign_name"])
        print("Scam Type:", result["scam_type"])

        print()
        print("Connected Network")
        print("------------------")
        print("Incidents:", result["incident_count"])
        print("Accounts:", result["account_count"])
        print("URLs:", result["url_count"])
        print("Phones:", result["phone_count"])
        print("UPI IDs:", result["upi_count"])

        print()
        print("Severity Breakdown")
        print("------------------")

        for severity, count in result["severity_breakdown"].items():
            print(f"{severity}: {count}")

        print()
        print("Campaign Risk")
        print("-------------")
        print("Risk Score:", result["risk_score"], "/100")
        print("Risk Level:", result["risk_level"])

