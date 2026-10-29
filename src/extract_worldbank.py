import requests
import boto3
import json
from datetime import datetime, timezone

BASE_URL = "https://api.worldbank.org/v2"
INDICATOR = "NY.GDP.PCAP.CD"

BUCKET_NAME = "datawithrudra-worldbank-data-2026"
AWS_PROFILE = "worldbank-dev"


def extract_worldbank_data():
    url = (
        f"{BASE_URL}/country/all/indicator/{INDICATOR}"
        "?format=json"
        "&date=2020:2025"
        "&per_page=20000"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Unexpected World Bank API response structure.")

    if data[1] is None:
        raise ValueError("World Bank API returned no observations.")

    print("API request successful")
    print(f"Number of observations: {len(data[1])}")

    return data


def upload_to_s3(data):
    session = boto3.Session(profile_name=AWS_PROFILE)

    s3 = session.client("s3")

    ingestion_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    s3_key = (
        f"raw/worldbank/"
        f"indicator={INDICATOR}/"
        f"ingestion_date={ingestion_date}/"
        f"data.json"
    )

    json_data = json.dumps(data)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json_data,
        ContentType="application/json"
    )

    print("Upload successful")
    print(f"s3://{BUCKET_NAME}/{s3_key}")


def main():
    data = extract_worldbank_data()
    upload_to_s3(data)


if __name__ == "__main__":
    main()