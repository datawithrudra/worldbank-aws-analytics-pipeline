import boto3
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone


AWS_PROFILE = "worldbank-dev"
BUCKET_NAME = "datawithrudra-worldbank-data-2026"

RAW_PREFIX = "raw/worldbank_metadata/"


def get_s3_client():
    """
    Create an authenticated S3 client using our local AWS profile.
    """
    session = boto3.Session(profile_name=AWS_PROFILE)

    return session.client("s3")


def find_latest_metadata_file(s3):
    """
    Find the most recently uploaded countries.json file
    under raw/worldbank_metadata/.
    """

    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=RAW_PREFIX
    )

    if "Contents" not in response:
        raise ValueError(
            "No country metadata files found in S3."
        )

    json_objects = [
        obj
        for obj in response["Contents"]
        if obj["Key"].endswith("countries.json")
    ]

    if not json_objects:
        raise ValueError(
            "No countries.json file found."
        )

    latest_object = max(
        json_objects,
        key=lambda obj: obj["LastModified"]
    )

    latest_key = latest_object["Key"]

    print("Latest metadata file:")
    print(latest_key)

    return latest_key


def read_country_metadata(s3, key):
    """
    Read the raw World Bank country metadata JSON from S3.
    """

    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=key
    )

    raw_json = (
        response["Body"]
        .read()
        .decode("utf-8")
    )

    data = json.loads(raw_json)

    if not isinstance(data, list) or len(data) < 2:
        raise ValueError(
            "Unexpected World Bank country metadata structure."
        )

    records = data[1]

    print(
        f"Raw country metadata records: {len(records)}"
    )

    return records


def flatten_country_metadata(records):
    """
    Convert nested World Bank JSON records
    into a flat Pandas DataFrame.
    """

    rows = []

    for record in records:

        rows.append({
            "country_code": record.get("id"),
            "iso2_code": record.get("iso2Code"),
            "country_name": record.get("name"),
            "region": (
                record.get("region", {})
                .get("value")
            ),
            "income_level": (
                record.get("incomeLevel", {})
                .get("value")
            ),
            "lending_type": (
                record.get("lendingType", {})
                .get("value")
            ),
            "capital_city": record.get("capitalCity"),
            "longitude": record.get("longitude"),
            "latitude": record.get("latitude")
        })

    df = pd.DataFrame(rows)

    print(
        f"Rows after flattening: {len(df)}"
    )

    return df


def clean_country_dimension(df):
    """
    Remove aggregate entities and validate
    the country dimension.
    """

    print("\n--- Country Data Quality Checks ---")

    print(
        f"Initial rows: {len(df)}"
    )

    print(
        "Missing country codes:",
        df["country_code"].isna().sum()
    )

    print(
        "Duplicate country codes:",
        df["country_code"].duplicated().sum()
    )

    print(
        "Aggregate rows:",
        (df["region"] == "Aggregates").sum()
    )

    # Remove World Bank aggregate entities
    df = df[
        df["region"] != "Aggregates"
    ].copy()

    # Remove records without valid country codes
    df = df.dropna(
        subset=[
            "country_code",
            "country_name"
        ]
    )

    # Country code should uniquely identify each country
    df = df.drop_duplicates(
        subset=["country_code"]
    )

    # Convert coordinates to numeric values
    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    # Sort for readability
    df = df.sort_values(
        "country_name"
    ).reset_index(drop=True)

    print(
        f"Final real-country rows: {len(df)}"
    )

    return df


def upload_country_dimension(s3, df):
    """
    Convert the clean DataFrame to Parquet
    and upload it to the processed layer.
    """

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

    key = (
        "processed/dimensions/"
        "dim_country/"
        f"processing_date={processing_date}/"
        "dim_country.parquet"
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )

    print("\nCountry dimension uploaded successfully")

    print(
        f"s3://{BUCKET_NAME}/{key}"
    )


def main():

    s3 = get_s3_client()

    latest_key = find_latest_metadata_file(s3)

    records = read_country_metadata(
        s3,
        latest_key
    )

    df = flatten_country_metadata(
        records
    )

    df = clean_country_dimension(
        df
    )

    print("\nPreview:")
    print(df.head(10))

    upload_country_dimension(
        s3,
        df
    )


if __name__ == "__main__":
    main()