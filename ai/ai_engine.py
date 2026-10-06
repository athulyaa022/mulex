import json

from entity_extractor import extract_entities
from risk_score import calculate_risk
from similarity import find_similar_incidents
from campaign_detector import detect_campaign


# ============================================
# MULEX - SCAM CLASSIFICATION
# ============================================

def classify_scam(message: str) -> str:
    """
    Classify a suspicious message into a scam category
    using explainable keyword-based rules.
    """

    text = message.lower()

    if any(word in text for word in [
        "kyc",
        "account will be blocked",
        "kyc expired"
    ]):
        return "KYC Scam"

    if any(word in text for word in [
        "bank",
        "bank account",
        "debit card",
        "credit card"
    ]):
        return "Bank Impersonation"

    if any(word in text for word in [
        "investment",
        "profit",
        "returns",
        "trading"
    ]):
        return "Investment Scam"

    if any(word in text for word in [
        "job",
        "salary",
        "vacancy",
        "hiring"
    ]):
        return "Job Scam"

    if any(word in text for word in [
        "parcel",
        "delivery",
        "courier",
        "package"
    ]):
        return "Delivery Scam"

    if any(word in text for word in [
        "upi",
        "payment",
        "pay now"
    ]):
        return "UPI Scam"

    if any(word in text for word in [
        "computer",
        "virus",
        "technical support",
        "microsoft"
    ]):
        return "Tech Support Scam"

    if any(word in text for word in [
        "lottery",
        "winner",
        "prize"
    ]):
        return "Lottery Scam"

    if any(word in text for word in [
        "video call",
        "voice call",
        "deepfake",
        "ai generated"
    ]):
        return "AI Impersonation"

    return "General Scam"


# ============================================
# MULEX - COMPLETE AI ANALYSIS PIPELINE
# ============================================

def analyze_message(message: str) -> dict:
    """
    Complete MULEX fraud intelligence pipeline.

    Pipeline:
    1. Entity extraction
    2. Scam classification
    3. Initial risk scoring
    4. Similar incident detection
    5. Campaign detection
    6. Campaign-based risk adjustment
    7. Explainable final intelligence
    """

    # ----------------------------------------
    # 1. Extract entities
    # ----------------------------------------

    entities = extract_entities(message)

    # ----------------------------------------
    # 2. Classify scam
    # ----------------------------------------

    scam_type = classify_scam(message)

    # ----------------------------------------
    # 3. Calculate initial risk
    # ----------------------------------------

    score, risk_level, reasons = calculate_risk(
        entities,
        message
    )

    # ----------------------------------------
    # 4. Load previous incidents
    # ----------------------------------------

    with open(
        "incidents.json",
        "r",
        encoding="utf-8"
    ) as file:
        incidents = json.load(file)

    # ----------------------------------------
    # 5. Find semantically similar incidents
    # ----------------------------------------

    similar_incidents = find_similar_incidents(
        message
    )

    # ----------------------------------------
    # 6. Create new incident representation
    # ----------------------------------------

    new_incident = {
        "incident_id": 999,
        "message": message,
        "scam_type": scam_type,

        "upi": (
            entities["upis"][0]
            if entities["upis"]
            else None
        ),

        "url": (
            entities["urls"][0]
            if entities["urls"]
            else None
        ),

        "phone": (
            entities["phones"][0]
            if entities["phones"]
            else None
        )
    }

    # ----------------------------------------
    # 7. Detect fraud campaign
    # ----------------------------------------

    campaign = detect_campaign(
        new_incident,
        incidents
    )

    # ----------------------------------------
    # 8. Add campaign evidence to risk
    # ----------------------------------------

    if campaign["campaign_status"] == "STRONG CAMPAIGN":

        score += 10

        reasons.append(
            "Strongly connected to a known fraud campaign"
        )

    elif campaign["campaign_status"] == "POSSIBLE CAMPAIGN":

        score += 5

        reasons.append(
            "Possibly connected to previous fraud incidents"
        )

    elif campaign["campaign_status"] == "WEAK CONNECTION":

        reasons.append(
            "Has a weak connection to a previous fraud incident"
        )

    if campaign["shared_indicators"]:

        reasons.append(
            "Shares identifiers with previous incidents"
        )

    # ----------------------------------------
    # 9. Keep risk score within 0-100
    # ----------------------------------------

    score = min(score, 100)

    # ----------------------------------------
    # 10. Determine final risk level
    # ----------------------------------------

    if score >= 70:
        risk_level = "HIGH"

    elif score >= 40:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    # ----------------------------------------
    # 11. Return final intelligence
    # ----------------------------------------

    return {
        "scam_type": scam_type,
        "risk_score": score,
        "risk_level": risk_level,
        "entities": entities,
        "similar_incidents": similar_incidents,
        "campaign": campaign,
        "reasons": reasons
    }


# ============================================
# DEMO / TEST
# ============================================

if __name__ == "__main__":

    sample_message = (
        "Your SBI KYC has expired. "
        "Complete verification immediately "
        "at fakebank.com "
        "or pay ₹500 via abc@upi."
    )

    result = analyze_message(sample_message)

    print()
    print("========================================")
    print("          MULEX AI ANALYSIS")
    print("========================================")

    print()
    print("Scam Type:")
    print(result["scam_type"])

    print()
    print("Risk:")
    print(
        f'{result["risk_score"]} / 100 '
        f'{result["risk_level"]}'
    )

    print()
    print("Entities:")
    print(result["entities"])

    print()
    print("Similar Incidents:")

    if result["similar_incidents"]:

        for incident in result["similar_incidents"]:
            print(
                f'Incident {incident["incident_id"]} '
                f'→ similarity: {incident["similarity"]} '
                f'→ {incident["scam_type"]}'
            )

    else:
        print("No similar incidents found.")

    print()
    print("Campaign:")
    print(
        f'Status: '
        f'{result["campaign"]["campaign_status"]}'
    )

    print(
        f'Confidence: '
        f'{result["campaign"]["confidence"]}'
    )

    print()
    print("Linked Incidents:")

    if result["campaign"]["linked_incidents"]:

        for incident in result["campaign"]["linked_incidents"]:
            print(
                f'Incident {incident["incident_id"]} '
                f'→ similarity: {incident["similarity"]} '
                f'→ connection score: '
                f'{incident["connection_score"]}'
            )

    else:
        print("No linked incidents.")

    print()
    print("Shared Indicators:")

    if result["campaign"]["shared_indicators"]:

        for indicator in result["campaign"]["shared_indicators"]:
            print(f"- {indicator}")

    else:
        print("None")

    print()
    print("Explainable Reasons:")

    for reason in result["reasons"]:
        print(f"✓ {reason}")

    print()
    print("========================================")
    print("       END OF MULEX ANALYSIS")
    print("========================================")