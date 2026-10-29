import requests
import boto3
import json
from datetime import datetime, timezone

BASE_URL = "https://api.worldbank.org/v2"
BUCKET_NAME = "datawithrudra-worldbank-data-2026"
AWS_PROFILE = "worldbank-dev"


def extract_country_metadata():
    url = (
        f"{BASE_URL}/country"
        "?format=json"
        "&per_page=400"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Unexpected country metadata response.")

    print(f"Country records received: {len(data[1])}")

    return data


def upload_country_metadata(data):
    session = boto3.Session(profile_name=AWS_PROFILE)
    s3 = session.client("s3")

    ingestion_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    key = (
        "raw/worldbank_metadata/"
        f"ingestion_date={ingestion_date}/"
        "countries.json"
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(data),
        ContentType="application/json"
    )

    print("Country metadata uploaded successfully")
    print(f"s3://{BUCKET_NAME}/{key}")


def main():
    data = extract_country_metadata()
    upload_country_metadata(data)


if __name__ == "__main__":
    main()