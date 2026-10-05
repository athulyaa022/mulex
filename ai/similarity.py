import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(message1: str, message2: str) -> float:

    embeddings = model.encode([message1, message2])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return round(float(similarity), 3)


def find_similar_incidents(
    new_message: str,
    threshold: float = 0.45
) -> list:

    # Load existing incidents
    with open("incidents.json", "r", encoding="utf-8") as file:
        incidents = json.load(file)

    # Create embedding for the new message
    new_embedding = model.encode([new_message])

    results = []

    for incident in incidents:

        old_embedding = model.encode([incident["message"]])

        similarity = cosine_similarity(
            new_embedding,
            old_embedding
        )[0][0]

        similarity = round(float(similarity), 3)

        if similarity >= threshold:

            results.append({
                "incident_id": incident["incident_id"],
                "similarity": similarity,
                "scam_type": incident["scam_type"]
            })

    # Highest similarity first
    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results


if __name__ == "__main__":

    new_message = (
        "Your bank KYC is expired. "
        "Complete verification immediately "
        "or your account will be suspended."
    )

    print("New Incident:")
    print(new_message)

    print("\nRelated Incidents:")

    results = find_similar_incidents(new_message)

    for result in results:
        print(result)