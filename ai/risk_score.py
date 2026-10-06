def calculate_risk(entities: dict, message: str) -> tuple[int, str, list[str]]:
    """
    Calculate an explainable fraud risk score.

    The score is based on:
    - Suspicious URLs
    - UPI/payment identifiers
    - Urgency or threat language
    - Financial amounts
    - Suspicious scam-related keywords
    """

    score = 0
    reasons = []

    text = message.lower()

    # --------------------------------
    # 1. Suspicious URL
    # --------------------------------

    if entities.get("urls"):
        score += 25
        reasons.append(
            "Contains suspicious external URL"
        )

    # --------------------------------
    # 2. UPI / payment identifier
    # --------------------------------

    if entities.get("upis"):
        score += 25
        reasons.append(
            "Contains direct financial payment identifier (UPI)"
        )

    # --------------------------------
    # 3. Phone number
    # --------------------------------

    if entities.get("phones"):
        score += 10
        reasons.append(
            "Contains a phone number for potential contact"
        )

    # --------------------------------
    # 4. Financial amount
    # --------------------------------

    if entities.get("amounts"):
        score += 10
        reasons.append(
            "Requests or mentions a financial amount"
        )

    # --------------------------------
    # 5. Urgency / threat language
    # --------------------------------

    urgency_keywords = [
        "urgent",
        "immediately",
        "act now",
        "within 24 hours",
        "expires",
        "expired",
        "blocked",
        "block",
        "suspend",
        "suspended",
        "deactivate",
        "verify now"
    ]

    if any(keyword in text for keyword in urgency_keywords):
        score += 20
        reasons.append(
            "Uses urgency or account-threat language"
        )

    # --------------------------------
    # 6. Scam-related financial language
    # --------------------------------

    financial_keywords = [
        "kyc",
        "bank",
        "payment",
        "transfer",
        "refund",
        "prize",
        "lottery",
        "investment",
        "otp",
        "password",
        "pin",
        "cvv"
    ]

    if any(keyword in text for keyword in financial_keywords):
        score += 10
        reasons.append(
            "Contains financial or scam-related keywords"
        )

    # --------------------------------
    # 7. Cap score at 100
    # --------------------------------

    score = min(score, 100)

    # --------------------------------
    # 8. Determine risk level
    # --------------------------------

    if score >= 70:
        risk_level = "HIGH"
    elif score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return score, risk_level, reasons