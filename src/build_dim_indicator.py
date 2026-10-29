import boto3
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone

from config import INDICATORS


AWS_PROFILE = "worldbank-dev"
BUCKET_NAME = "datawithrudra-worldbank-data-2026"


INDICATOR_METADATA = {
    "NY.GDP.MKTP.CD": {
        "short_name": "gdp",
        "indicator_name": "GDP (current US$)",
        "category": "Economy"
    },
    "NY.GDP.PCAP.CD": {
        "short_name": "gdp_per_capita",
        "indicator_name": "GDP per capita (current US$)",
        "category": "Economy"
    },
    "SP.POP.TOTL": {
        "short_name": "population",
        "indicator_name": "Population, total",
        "category": "Demographics"
    },
    "SP.DYN.LE00.IN": {
        "short_name": "life_expectancy",
        "indicator_name": "Life expectancy at birth",
        "category": "Health"
    },
    "IT.NET.USER.ZS": {
        "short_name": "internet_usage",
        "indicator_name": "Individuals using the Internet (%)",
        "category": "Technology"
    },
    "SL.UEM.TOTL.ZS": {
        "short_name": "unemployment",
        "indicator_name": "Unemployment (% of labor force)",
        "category": "Labour"
    }
}


def get_s3_client():
    session = boto3.Session(
        profile_name=AWS_PROFILE
    )

    return session.client("s3")


def build_indicator_dimension():
    rows = []

    for indicator_code in INDICATORS.keys():

        metadata = INDICATOR_METADATA[indicator_code]

        rows.append({
            "indicator_code": indicator_code,
            "indicator_name": metadata["indicator_name"],
            "short_name": metadata["short_name"],
            "category": metadata["category"]
        })

    df = pd.DataFrame(rows)

    print("Indicator dimension created")
    print(df)

    return df


def validate_indicator_dimension(df):

    print("\n--- Indicator Dimension Quality Checks ---")

    print(
        "Duplicate indicator codes:",
        df["indicator_code"].duplicated().sum()
    )

    print(
        "Missing indicator names:",
        df["indicator_name"].isna().sum()
    )

    if df["indicator_code"].duplicated().any():
        raise ValueError(
            "Indicator codes must be unique."
        )

    if df["indicator_name"].isna().any():
        raise ValueError(
            "Indicator names cannot be missing."
        )


def upload_indicator_dimension(s3, df):

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
        "dim_indicator/"
        f"processing_date={processing_date}/"
        "dim_indicator.parquet"
    )

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream"
    )

    print("\nIndicator dimension uploaded")
    print(f"s3://{BUCKET_NAME}/{key}")


def main():

    s3 = get_s3_client()

    df = build_indicator_dimension()

    validate_indicator_dimension(df)

    upload_indicator_dimension(
        s3,
        df
    )


if __name__ == "__main__":
    main()