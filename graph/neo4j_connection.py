import os


def configure_credentials(uri: str, username: str, password: str) -> None:
    """Configure Neo4j credentials for the Person 4 graph modules."""
    if not uri or not username or not password:
        raise ValueError("Neo4j credentials are not configured")

    os.environ["NEO4J_URI"] = uri
    os.environ["NEO4J_USERNAME"] = username
    os.environ["NEO4J_PASSWORD"] = password