from fastapi import FastAPI, HTTPException

from graph_service import get_account_network
from graph_queries import get_campaign_intelligence
from neo4j_connection import verify_connectivity


app = FastAPI(
    title="MULEX Graph Intelligence API",
    description="Graph and mule-risk analysis service for MULEX",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "MULEX Graph Intelligence API",
        "status": "running"
    }


@app.get("/health")
def health():
    try:
        verify_connectivity()
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail={"error": "Neo4j unavailable", "message": str(error)},
        ) from error
    return {"service": "MULEX Graph Intelligence", "status": "healthy", "neo4j": "connected"}


@app.get("/graph/account/{account_id}")
def account_graph(account_id: str):
    try:
        result = get_account_network(account_id)

        if not result["nodes"]:
            raise HTTPException(
                status_code=404,
                detail=f"Account {account_id} not found"
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/graph/campaign/{campaign_id}")
def campaign_graph(campaign_id: str):
    try:
        result = get_campaign_intelligence(campaign_id)

        if result is None or "error" in result:
            raise HTTPException(
                status_code=404,
                detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign does not exist"},
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )