import json
import os
import random
from datetime import datetime, timedelta


# ============================================================
# SETTINGS
# ============================================================

random.seed(42)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# BASIC COUNTS
# ============================================================

NUM_ACCOUNTS = 1000
NUM_TRANSACTIONS = 5000
NUM_INCIDENTS = 200
NUM_PHONES = 100
NUM_UPI_IDS = 100
NUM_URLS = 50
NUM_CAMPAIGNS = 20

# Accounts deliberately used as mule accounts
MULE_ACCOUNTS = [
    f"ACC{i:04d}"
    for i in range(900, 921)
]


# ============================================================
# CREATE ACCOUNTS
# ============================================================

accounts = []

for i in range(1, NUM_ACCOUNTS + 1):

    account_id = f"ACC{i:04d}"

    accounts.append({
        "id": account_id,
        "type": "normal"
    })


# ============================================================
# CREATE PHONES
# ============================================================

phones = []

for i in range(1, NUM_PHONES + 1):

    phones.append({
        "id": f"PHONE{i:03d}",
        "number": f"+91-98{random.randint(10000000, 99999999)}"
    })


# ============================================================
# CREATE UPI IDS
# ============================================================

upi_ids = []

for i in range(1, NUM_UPI_IDS + 1):

    upi_ids.append({
        "id": f"UPI{i:03d}",
        "value": f"user{i}@upi"
    })


# ============================================================
# CREATE URLS
# ============================================================

urls = []

for i in range(1, NUM_URLS + 1):

    urls.append({
        "id": f"URL{i:03d}",
        "value": f"https://fake-site-{i}.example.com"
    })


# ============================================================
# CREATE CAMPAIGNS
# ============================================================

scam_types = [
    "UPI Fraud",
    "Phishing",
    "Investment Scam",
    "Job Scam",
    "Loan Scam",
    "Lottery Scam",
    "Account Takeover",
    "Marketplace Scam"
]

campaigns = []

for i in range(1, NUM_CAMPAIGNS + 1):

    scam_type = random.choice(scam_types)

    campaigns.append({
        "id": f"CAMP{i:03d}",
        "name": f"Fraud Campaign {i}",
        "scam_type": scam_type
    })


# ============================================================
# CREATE INCIDENTS
# ============================================================

incidents = []

start_date = datetime(2026, 8, 1)

for i in range(1, NUM_INCIDENTS + 1):

    campaign = random.choice(campaigns)

    incident_date = start_date + timedelta(
        days=random.randint(0, 60)
    )

    incidents.append({
        "id": f"INC{i:04d}",
        "scam_type": campaign["scam_type"],
        "severity": random.choice([
            "Low",
            "Medium",
            "High",
            "Critical"
        ]),
        "reported_date": incident_date.strftime("%Y-%m-%d"),
        "campaign_id": campaign["id"]
    })


# ============================================================
# CREATE NORMAL TRANSACTIONS
# ============================================================

transactions = []

transaction_start = datetime(2026, 8, 1)

for i in range(1, NUM_TRANSACTIONS + 1):

    sender = random.choice(accounts)["id"]
    receiver = random.choice(accounts)["id"]

    # Avoid self-transactions
    while receiver == sender:
        receiver = random.choice(accounts)["id"]

    transaction_date = transaction_start + timedelta(
        minutes=random.randint(0, 60 * 24 * 60)
    )

    transactions.append({
        "id": f"TXN{i:05d}",
        "sender": sender,
        "receiver": receiver,
        "amount": random.randint(500, 50000),
        "date": transaction_date.strftime("%Y-%m-%d %H:%M:%S")
    })


# ============================================================
# PLANT REALISTIC MULE NETWORKS
# ============================================================

print("Planting suspicious mule networks...")

next_transaction_id = NUM_TRANSACTIONS + 1

# Accounts used as victims/senders
victim_accounts = [
    f"ACC{i:04d}"
    for i in range(1, 900)
]

# Accounts used as downstream receivers
receiver_accounts = [
    f"ACC{i:04d}"
    for i in range(1, 900)
]


for mule_index, mule_id in enumerate(MULE_ACCOUNTS):

    # --------------------------------------------------------
    # 12 different accounts send money to each mule
    # --------------------------------------------------------

    selected_victims = random.sample(
        victim_accounts,
        12
    )

    # Use a recent time window to create transaction velocity
    base_time = datetime(2026, 10, 4, 10, 0, 0)

    for victim_index, victim_id in enumerate(selected_victims):

        transaction_time = base_time + timedelta(
            minutes=(mule_index * 2) + victim_index
        )

        transactions.append({
            "id": f"TXN{next_transaction_id:05d}",
            "sender": victim_id,
            "receiver": mule_id,
            "amount": random.randint(5000, 25000),
            "date": transaction_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

        next_transaction_id += 1


    # --------------------------------------------------------
    # Mule quickly sends money to other accounts
    # --------------------------------------------------------

    selected_receivers = random.sample(
        receiver_accounts,
        2
    )

    for receiver_index, receiver_id in enumerate(
        selected_receivers
    ):

        transaction_time = base_time + timedelta(
            minutes=20 + (receiver_index * 3)
        )

        transactions.append({
            "id": f"TXN{next_transaction_id:05d}",
            "sender": mule_id,
            "receiver": receiver_id,
            "amount": random.randint(8000, 30000),
            "date": transaction_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

        next_transaction_id += 1


# ============================================================
# SAVE DATA
# ============================================================

data = {
    "accounts": accounts,
    "phones": phones,
    "upi_ids": upi_ids,
    "urls": urls,
    "campaigns": campaigns,
    "incidents": incidents,
    "transactions": transactions,
    "mule_accounts": MULE_ACCOUNTS
}


output_file = os.path.join(
    DATA_DIR,
    "mulex_data.json"
)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        data,
        file,
        indent=2
    )


# ============================================================
# SUMMARY
# ============================================================

print("")
print("=================================")
print("MULEX SYNTHETIC DATA GENERATED")
print("=================================")

print(f"Accounts       : {len(accounts)}")
print(f"Transactions   : {len(transactions)}")
print(f"Incidents      : {len(incidents)}")
print(f"Campaigns      : {len(campaigns)}")
print(f"Phones         : {len(phones)}")
print(f"UPI IDs        : {len(upi_ids)}")
print(f"URLs           : {len(urls)}")
print(f"Mule accounts  : {len(MULE_ACCOUNTS)}")

print("---------------------------------")
print(f"Saved to: {output_file}")
print("---------------------------------")