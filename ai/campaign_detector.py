import json

from similarity import calculate_similarity


def detect_campaign(new_incident: dict, incidents: list) -> dict:
    """
    Detect whether a new incident is connected
    to previous incidents.
    """

    linked_incidents = []
    shared_indicators = []

    new_message = new_incident["message"]
    new_scam_type = new_incident.get("scam_type", "")

    new_upi = new_incident.get("upi")
    new_url = new_incident.get("url")
    new_phone = new_incident.get("phone")

    for incident in incidents:

        # -------------------------
        # 1. Semantic similarity
        # -------------------------

        similarity = calculate_similarity(
            new_message,
            incident["message"]
        )

        # -------------------------
        # 2. Scam type similarity
        # -------------------------

        same_scam_type = (
            new_scam_type
            and incident.get("scam_type") == new_scam_type
        )

        # -------------------------
        # 3. Shared identifiers
        # -------------------------

        shared = []

        if new_upi and new_upi == incident.get("upi"):
            shared.append(new_upi)

        if new_url and new_url == incident.get("url"):
            shared.append(new_url)

        if new_phone and new_phone == incident.get("phone"):
            shared.append(new_phone)

        # -------------------------
        # 4. Calculate connection score
        # -------------------------

        score = 0

        # Semantic similarity
        if similarity >= 0.60:
            score += 40

        elif similarity >= 0.45:
            score += 25

        # Same scam type
        if same_scam_type:
            score += 20

        # Shared identifiers
        score += min(len(shared) * 20, 40)

        # -------------------------
        # 5. Decide whether linked
        # -------------------------

        if score >= 40:

            linked_incidents.append({
                "incident_id": incident["incident_id"],
                "similarity": similarity,
                "connection_score": score,
                "scam_type": incident.get("scam_type")
            })

            shared_indicators.extend(shared)

    # Remove duplicates
    shared_indicators = list(set(shared_indicators))

    # Sort highest connection first
    linked_incidents.sort(
        key=lambda x: x["connection_score"],
        reverse=True
    )

    # -------------------------
    # Campaign confidence
    # -------------------------

    if len(linked_incidents) >= 3:
        confidence = 0.90
        campaign_status = "STRONG CAMPAIGN"

    elif len(linked_incidents) == 2:
        confidence = 0.75
        campaign_status = "POSSIBLE CAMPAIGN"

    elif len(linked_incidents) == 1:
        confidence = 0.55
        campaign_status = "WEAK CONNECTION"

    else:
        confidence = 0.10
        campaign_status = "NO CAMPAIGN DETECTED"

    return {
        "campaign_status": campaign_status,
        "confidence": confidence,
        "linked_incidents": linked_incidents,
        "shared_indicators": shared_indicators
    }


if __name__ == "__main__":

    # Load existing incidents
    with open("incidents.json", "r", encoding="utf-8") as file:
        incidents = json.load(file)

    # New incident received by MULEX
    new_incident = {
        "incident_id": 201,

        "message": (
            "Your bank KYC is expired. "
            "Complete verification immediately "
            "or your account will be suspended."
        ),

        "scam_type": "KYC Scam",

        "upi": "abc@upi",

        "url": "fakebank.com"
    }

    result = detect_campaign(
        new_incident,
        incidents
    )

    print("\nMULEX CAMPAIGN ANALYSIS")
    print("========================")

    print(
        "Campaign Status:",
        result["campaign_status"]
    )

    print(
        "Confidence:",
        result["confidence"]
    )

    print(
        "\nLinked Incidents:"
    )

    for incident in result["linked_incidents"]:
        print(incident)

    print(
        "\nShared Indicators:"
    )

    for indicator in result["shared_indicators"]:
        print("-", indicator)