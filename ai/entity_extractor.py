import re


def extract_entities(text: str) -> dict:
    """
    Extract important fraud-related entities from a message.

    Entities extracted:
    - URLs
    - UPI IDs
    - Phone numbers
    - Email addresses
    - Money amounts
    """

    # --------------------------------
    # 1. URL extraction
    # --------------------------------

    url_pattern = (
        r'https?://[^\s]+'
        r'|(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        r'(?:/[^\s]*)?'
    )

    # --------------------------------
    # 2. UPI ID extraction
    # Example: abc@upi
    # --------------------------------

    upi_pattern = r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\b'

    # --------------------------------
    # 3. Indian phone number extraction
    # Examples:
    # 9876543210
    # +919876543210
    # +91 9876543210
    # --------------------------------

    phone_pattern = r'(?:\+91[\s-]?)?[6-9]\d{9}\b'

    # --------------------------------
    # 4. Email extraction
    # Example: support@example.com
    # --------------------------------

    email_pattern = (
        r'\b[A-Za-z0-9._%+-]+'
        r'@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b'
    )

    # --------------------------------
    # 5. Money amount extraction
    # Examples:
    # ₹500
    # Rs 500
    # Rs.500
    # INR 500
    # --------------------------------

    amount_pattern = (
        r'(?:₹|Rs\.?|INR)\s?'
        r'\d+(?:,\d{3})*(?:\.\d+)?'
    )

    # --------------------------------
    # Perform extraction
    # --------------------------------

    urls = re.findall(url_pattern, text)

    upis = re.findall(upi_pattern, text)

    phones = re.findall(phone_pattern, text)

    emails = re.findall(email_pattern, text)

    amounts = re.findall(
        amount_pattern,
        text,
        re.IGNORECASE
    )

    # --------------------------------
    # Remove email addresses
    # from UPI results
    # --------------------------------

    upis = [
        upi for upi in upis
        if upi not in emails
    ]

    # --------------------------------
    # Return structured entities
    # --------------------------------

    return {
        "urls": urls,
        "upis": upis,
        "phones": phones,
        "emails": emails,
        "amounts": amounts
    }