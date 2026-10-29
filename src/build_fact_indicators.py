import boto3
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone

from config import INDICATORS


AWS_PROFILE = "worldbank-dev"
BUCKET_NAME = "datawithrudra-worldbank-data-2026"

RAW_PREFIX = "raw/worldbank/"
DIM_COUNTRY_PREFIX = "processed/dimensions/dim_country/"


def get_s3_client():

    session = boto3.Session(
        profile_name=AWS_PROFILE
    )

    return session.client("s3")


def find_latest_object(
    s3,
    prefix,
    filename
):

    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=prefix
    )

    if "Contents" not in response:
        raise ValueError(
            f"No objects found under {prefix}"
        )

    candidates = [
        obj
        for obj in response["Contents"]
        if obj["Key"].endswith(filename)
    ]

    if not candidates:
        raise ValueError(
            f"No {filename} found under {prefix}"
        )

    latest = max(
        candidates,
        key=lambda obj: obj["LastModified"]
    )

    return latest["Key"]


def read_json_from_s3(
    s3,
    key
):

    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=key
    )

    content = (
        response["Body"]
        .read()
        .decode("utf-8")
    )

    return json.loads(content)


def read_parquet_from_s3(
    s3,
    key
):

    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=key
    )

    buffer = BytesIO(
        response["Body"].read()
    )

    return pd.read_parquet(
        buffer,
        engine="pyarrow"
    )


def flatten_indicator_records(
    records
):

    rows = []

    for record in records:

        rows.append({
            "country_code": record.get(
                "countryiso3code"
            ),
            "indicator_code": (
                record.get(
                    "indicator",
                    {}
                ).get("id")
            ),
            "year": record.get("date"),
            "value": record.get("value")
        })

    return pd.DataFrame(rows)


def load_all_indicators(
    s3
):

    frames = []

    for indicator_code in INDICATORS.keys():

        prefix = (
            f"{RAW_PREFIX}"
            f"indicator={indicator_code}/"
        )

        latest_key = find_latest_object(
            s3,
            prefix,
            "data.json"
        )

        print(
            f"Loading {indicator_code}"
        )

        print(
            f"Source: {latest_key}"
        )

        raw_data = read_json_from_s3(
            s3,
            latest_key
        )

        records = raw_data[1]

        df = flatten_indicator_records(
            records
        )

        frames.append(df)

    fact_df = pd.concat(
        frames,
        ignore_index=True
    )

    print(
        f"\nCombined rows: {len(fact_df)}"
    )

    return fact_df


def clean_fact_data(
    fact_df,
    dim_country
):

    print("\n--- Fact Data Quality Checks ---")

    print(
        "Duplicate rows:",
        fact_df.duplicated().sum()
    )

    print(
        "Missing country codes:",
        fact_df["country_code"]
        .isna()
        .sum()
    )

    print(
        "Missing years:",
        fact_df["year"]
        .isna()
        .sum()
    )

    print(
        "Missing values:",
        fact_df["value"]
        .isna()
        .sum()
    )

    # Enforce types
    fact_df["year"] = pd.to_numeric(
        fact_df["year"],
        errors="coerce"
    ).astype("Int64")

    fact_df["value"] = pd.to_numeric(
        fact_df["value"],
        errors="coerce"
    )

    # Keep only valid countries
    valid_country_codes = set(
        dim_country["country_code"]
    )

    before_filter = len(
        fact_df
    )

    fact_df = fact_df[
        fact_df["country_code"]
        .isin(valid_country_codes)
    ].copy()

    removed_aggregates = (
        before_filter
        - len(fact_df)
    )

    print(
        "Rows removed because they were "
        f"aggregates/non-countries: {removed_aggregates}"
    )

    # Remove unusable measurements
    fact_df = fact_df.dropna(
        subset=[
            "country_code",
            "indicator_code",
            "year",
            "value"
        ]
    )

    # One country + indicator + year
    # should normally be unique
    fact_df = fact_df.drop_duplicates(
        subset=[
            "country_code",
            "indicator_code",
            "year"
        ]
    )

    fact_df = fact_df.sort_values(
        [
            "country_code",
            "indicator_code",
            "year"
        ]
    ).reset_index(drop=True)

    print(
        f"Final fact rows: {len(fact_df)}"
    )

    return fact_df


def upload_fact_table(
    s3,
    fact_df
):

    buffer = BytesIO()

    fact_df.to_parquet(
        buffer,
        engine="pyarrow",
        index=False
    )

    buffer.seek(0)

    processing_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    key = (
        "processed/facts/"
        "fact_indicators/"
        f"processing_date={processing_date}/"
        "fact_indicators.parquet"
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )

    print("\nFact table uploaded successfully")

    print(
        f"s3://{BUCKET_NAME}/{key}"
    )


def main():

    s3 = get_s3_client()

    latest_country_key = find_latest_object(
        s3,
        DIM_COUNTRY_PREFIX,
        "dim_country.parquet"
    )

    print(
        "Using country dimension:"
    )

    print(
        latest_country_key
    )

    dim_country = read_parquet_from_s3(
        s3,
        latest_country_key
    )

    fact_df = load_all_indicators(
        s3
    )

    fact_df = clean_fact_data(
        fact_df,
        dim_country
    )

    print("\nFact table preview:")

    print(
        fact_df.head(10)
    )

    upload_fact_table(
        s3,
        fact_df
    )


if __name__ == "__main__":
    main()