import boto3
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone


AWS_PROFILE = "worldbank-dev"
BUCKET_NAME = "datawithrudra-worldbank-data-2026"

INDICATOR = "NY.GDP.PCAP.CD"

RAW_KEY = (
    "raw/worldbank/"
    f"indicator={INDICATOR}/"
    "ingestion_date=2026-10-11/"
    "data.json"
)


def get_s3_client():
    session = boto3.Session(profile_name=AWS_PROFILE)
    return session.client("s3")


def read_raw_data(s3):
    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=RAW_KEY
    )

    raw_json = response["Body"].read().decode("utf-8")

    data = json.loads(raw_json)

    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Unexpected raw World Bank data structure.")

    records = data[1]

    print(f"Raw observations loaded: {len(records)}")

    return records


def transform_data(records):
    rows = []

    for record in records:
        rows.append({
            "country_name": record["country"]["value"],
            "country_code": record["countryiso3code"],
            "indicator_name": record["indicator"]["value"],
            "indicator_code": record["indicator"]["id"],
            "year": record["date"],
            "value": record["value"]
        })

    df = pd.DataFrame(rows)

    print(f"Rows after flattening: {len(df)}")

    return df


def clean_data(df):
    print("\n--- Data Quality Checks ---")

    print(f"Duplicate rows: {df.duplicated().sum()}")
    print(f"Missing country codes: {df['country_code'].isna().sum()}")
    print(f"Missing years: {df['year'].isna().sum()}")
    print(f"Missing indicator values: {df['value'].isna().sum()}")

    # Remove rows that do not have a valid ISO3 country code
    df = df[
        df["country_code"].notna()
        & (df["country_code"] != "")
    ].copy()

    # Remove duplicate country/year/indicator combinations
    df = df.drop_duplicates(
        subset=["country_code", "indicator_code", "year"]
    )

    # Enforce data types
    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    ).astype("Int64")

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    # Remove rows without usable values
    df = df.dropna(
        subset=["country_code", "year", "value"]
    )

    print(f"Rows after cleaning: {len(df)}")

    return df


def upload_processed_data(s3, df):
    buffer = BytesIO()

    df.to_parquet(
        buffer,
        engine="pyarrow",
        index=False
    )

    buffer.seek(0)

    processing_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    processed_key = (
        "processed/worldbank/"
        f"indicator={INDICATOR}/"
        f"processing_date={processing_date}/"
        "data.parquet"
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=processed_key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )

    print("\nProcessed data uploaded successfully")
    print(
        f"s3://{BUCKET_NAME}/{processed_key}"
    )


def main():
    s3 = get_s3_client()

    records = read_raw_data(s3)

    df = transform_data(records)

    df = clean_data(df)

    print("\nPreview:")
    print(df.head())

    upload_processed_data(s3, df)


if __name__ == "__main__":
    main()