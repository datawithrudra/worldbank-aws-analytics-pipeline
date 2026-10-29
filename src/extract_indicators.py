import requests
import boto3
import json
from datetime import datetime, timezone

from config import INDICATORS


BASE_URL = "https://api.worldbank.org/v2"

BUCKET_NAME = "datawithrudra-worldbank-data-2026"

AWS_PROFILE = "worldbank-dev"

START_YEAR = 2020
END_YEAR = 2025


def get_s3_client():

    session = boto3.Session(
        profile_name=AWS_PROFILE
    )

    return session.client("s3")


def extract_indicator(indicator_code):

    url = (
        f"{BASE_URL}/country/all/"
        f"indicator/{indicator_code}"
        f"?format=json"
        f"&date={START_YEAR}:{END_YEAR}"
        f"&per_page=20000"
    )

    print(
        f"\nExtracting: {indicator_code}"
    )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            f"Unexpected API response for {indicator_code}"
        )

    if len(data) < 2 or data[1] is None:
        raise ValueError(
            f"No observations returned for {indicator_code}"
        )

    print(
        f"Observations received: {len(data[1])}"
    )

    return data


def upload_raw_indicator(
    s3,
    indicator_code,
    indicator_name,
    data
):

    ingestion_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    s3_key = (
        "raw/worldbank/"
        f"indicator={indicator_code}/"
        f"ingestion_date={ingestion_date}/"
        "data.json"
    )

    payload = json.dumps(data)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=payload,
        ContentType="application/json"
    )

    print(
        f"Uploaded {indicator_name}"
    )

    print(
        f"s3://{BUCKET_NAME}/{s3_key}"
    )


def main():

    s3 = get_s3_client()

    successful = 0
    failed = 0

    for indicator_code, indicator_name in INDICATORS.items():

        try:

            data = extract_indicator(
                indicator_code
            )

            upload_raw_indicator(
                s3,
                indicator_code,
                indicator_name,
                data
            )

            successful += 1

        except Exception as error:

            failed += 1

            print(
                f"FAILED: {indicator_name}"
            )

            print(
                f"Reason: {error}"
            )

    print("\n-------------------------")
    print("PIPELINE SUMMARY")
    print("-------------------------")

    print(
        f"Successful indicators: {successful}"
    )

    print(
        f"Failed indicators: {failed}"
    )


if __name__ == "__main__":
    main()