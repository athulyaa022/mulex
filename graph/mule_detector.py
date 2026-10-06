import os
from datetime import datetime

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

env_path = os.path.join(
    os.path.dirname(__file__),
    ".env"
)

load_dotenv(env_path, override=True)

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


# ============================================================
# NEO4J CONNECTION
# ============================================================

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)


# ============================================================
# CALCULATE MULE RISK
# ============================================================

def calculate_mule_risk(account_id):

    with driver.session() as session:

        # ----------------------------------------------------
        # GET INCOMING TRANSACTIONS
        # ----------------------------------------------------

        incoming_result = session.run(
            """
            MATCH (sender:Account)
                -[:SENT]->(t:Transaction)
                -[:RECEIVED_BY]->(a:Account {id: $account_id})

            RETURN
                t.id AS transaction_id,
                t.amount AS amount,
                t.date AS date,
                sender.id AS sender
            """,
            account_id=account_id
        )

        incoming_transactions = [
            record.data()
            for record in incoming_result
        ]


        # ----------------------------------------------------
        # GET OUTGOING TRANSACTIONS
        # ----------------------------------------------------

        outgoing_result = session.run(
            """
            MATCH (a:Account {id: $account_id})
                -[:SENT]->(t:Transaction)
                -[:RECEIVED_BY]->(receiver:Account)

            RETURN
                t.id AS transaction_id,
                t.amount AS amount,
                t.date AS date,
                receiver.id AS receiver
            """,
            account_id=account_id
        )

        outgoing_transactions = [
            record.data()
            for record in outgoing_result
        ]


        # ----------------------------------------------------
        # CHECK ACCOUNT
        # ----------------------------------------------------

        account_result = session.run(
            """
            MATCH (a:Account {id: $account_id})
            RETURN a.id AS account_id
            """,
            account_id=account_id
        )

        if account_result.single() is None:
            return None


        # ----------------------------------------------------
        # BASIC COUNTS
        # ----------------------------------------------------

        incoming_count = len(incoming_transactions)

        outgoing_count = len(outgoing_transactions)

        unique_senders = len(
            set(
                item["sender"]
                for item in incoming_transactions
            )
        )

        unique_receivers = len(
            set(
                item["receiver"]
                for item in outgoing_transactions
            )
        )


        # ----------------------------------------------------
        # MONEY FLOW
        # ----------------------------------------------------

        incoming_amount = sum(
            item["amount"] or 0
            for item in incoming_transactions
        )

        outgoing_amount = sum(
            item["amount"] or 0
            for item in outgoing_transactions
        )


        # ====================================================
        # RAPID PASS-THROUGH DETECTION
        # ====================================================

        parsed_incoming = []
        parsed_outgoing = []

        for item in incoming_transactions:

            try:
                parsed_incoming.append(
                    (
                        datetime.strptime(
                            item["date"],
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        item["amount"] or 0
                    )
                )

            except (ValueError, TypeError):
                pass


        for item in outgoing_transactions:

            try:
                parsed_outgoing.append(
                    (
                        datetime.strptime(
                            item["date"],
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        item["amount"] or 0
                    )
                )

            except (ValueError, TypeError):
                pass


        rapid_activity = False
        rapid_matches = 0
        fastest_pass_through = None


        # Look for money received and then money sent
        # within 30 minutes.

        for incoming_time, incoming_value in parsed_incoming:

            for outgoing_time, outgoing_value in parsed_outgoing:

                difference = (
                    outgoing_time - incoming_time
                ).total_seconds() / 60


                # Outgoing transaction must happen
                # after incoming transaction.

                if 0 <= difference <= 30:

                    rapid_activity = True
                    rapid_matches += 1


                    if (
                        fastest_pass_through is None
                        or difference < fastest_pass_through
                    ):

                        fastest_pass_through = difference


        # ====================================================
        # RISK SCORE
        # ====================================================

        score = 0

        evidence = []


        # ----------------------------------------------------
        # MANY INCOMING TRANSACTIONS
        # ----------------------------------------------------

        if incoming_count >= 10:

            score += 25

            evidence.append(
                f"High incoming transaction count: "
                f"{incoming_count}"
            )

        elif incoming_count >= 5:

            score += 15

            evidence.append(
                f"Moderate incoming transaction count: "
                f"{incoming_count}"
            )


        # ----------------------------------------------------
        # MANY UNIQUE SENDERS
        # ----------------------------------------------------

        if unique_senders >= 10:

            score += 30

            evidence.append(
                f"Money received from many different "
                f"accounts: {unique_senders}"
            )

        elif unique_senders >= 5:

            score += 15

            evidence.append(
                f"Money received from multiple "
                f"accounts: {unique_senders}"
            )


        # ----------------------------------------------------
        # OUTGOING ACTIVITY
        # ----------------------------------------------------

        if outgoing_count >= 5:

            score += 20

            evidence.append(
                f"High outgoing transaction activity: "
                f"{outgoing_count}"
            )

        elif outgoing_count >= 2:

            score += 10

            evidence.append(
                f"Multiple outgoing transactions: "
                f"{outgoing_count}"
            )


        # ----------------------------------------------------
        # MULTIPLE RECEIVERS
        # ----------------------------------------------------

        if unique_receivers >= 3:

            score += 15

            evidence.append(
                f"Money sent to multiple accounts: "
                f"{unique_receivers}"
            )

        elif unique_receivers >= 2:

            score += 10

            evidence.append(
                f"Money sent to multiple accounts: "
                f"{unique_receivers}"
            )


        # ----------------------------------------------------
        # RAPID PASS-THROUGH
        # ----------------------------------------------------

        if rapid_activity:

            score += 10

            evidence.append(
                f"Rapid money movement detected: "
                f"{rapid_matches} incoming/outgoing "
                f"transaction pairs within 30 minutes"
            )

            if fastest_pass_through is not None:

                evidence.append(
                    f"Fastest pass-through: "
                    f"{fastest_pass_through:.1f} minutes"
                )


        # ----------------------------------------------------
        # LARGE PORTION OF MONEY TRANSFERRED OUT
        # ----------------------------------------------------

        if (
            incoming_amount > 0
            and outgoing_amount > 0
            and outgoing_amount >= incoming_amount * 0.5
        ):

            score += 10

            evidence.append(
                "Large portion of received money "
                "is transferred out"
            )


        # ----------------------------------------------------
        # LIMIT SCORE
        # ----------------------------------------------------

        score = min(score, 100)


        # ----------------------------------------------------
        # RISK LEVEL
        # ----------------------------------------------------

        if score >= 70:

            risk_level = "HIGH"

        elif score >= 40:

            risk_level = "MEDIUM"

        else:

            risk_level = "LOW"


        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {
            "account_id": account_id,

            "risk_score": score,

            "risk_level": risk_level,

            "incoming_transactions": incoming_count,

            "outgoing_transactions": outgoing_count,

            "unique_senders": unique_senders,

            "unique_receivers": unique_receivers,

            "incoming_amount": incoming_amount,

            "outgoing_amount": outgoing_amount,

            "rapid_activity": rapid_activity,

            "rapid_matches": rapid_matches,

            "fastest_pass_through": fastest_pass_through,

            "evidence": evidence
        }


# ============================================================
# TEST DETECTOR
# ============================================================

if __name__ == "__main__":

    test_accounts = [
        "ACC0900",
        "ACC0905",
        "ACC0910",
        "ACC0920",
        "ACC0001"
    ]


    print("")
    print("========================================")
    print("MULEX MULE RISK DETECTOR")
    print("========================================")


    for account_id in test_accounts:

        result = calculate_mule_risk(
            account_id
        )


        print("")
        print("----------------------------------------")


        if result is None:

            print(
                f"Account not found: {account_id}"
            )

            continue


        print(
            f"Account          : "
            f"{result['account_id']}"
        )

        print(
            f"Risk Score       : "
            f"{result['risk_score']}/100"
        )

        print(
            f"Risk Level       : "
            f"{result['risk_level']}"
        )

        print(
            f"Incoming         : "
            f"{result['incoming_transactions']}"
        )

        print(
            f"Outgoing         : "
            f"{result['outgoing_transactions']}"
        )

        print(
            f"Unique senders   : "
            f"{result['unique_senders']}"
        )

        print(
            f"Unique receivers : "
            f"{result['unique_receivers']}"
        )

        print(
            f"Incoming amount  : "
            f"{result['incoming_amount']}"
        )

        print(
            f"Outgoing amount  : "
            f"{result['outgoing_amount']}"
        )

        print(
            f"Rapid activity   : "
            f"{result['rapid_activity']}"
        )

        print(
            f"Rapid pairs      : "
            f"{result['rapid_matches']}"
        )


        if result["fastest_pass_through"] is not None:

            print(
                f"Fastest pass-through: "
                f"{result['fastest_pass_through']:.1f} minutes"
            )


        print("Evidence:")

        for item in result["evidence"]:

            print(
                f"  - {item}"
            )


    print("")
    print("========================================")


    driver.close()