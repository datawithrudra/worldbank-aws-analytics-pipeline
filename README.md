# World Bank AWS Cloud Analytics Pipeline

An end-to-end **cloud data engineering and business intelligence project** that extracts global development indicators from the World Bank API, transforms and models the data using Python, stores analytics-ready datasets in Amazon S3, catalogs them with AWS Glue, queries them with Amazon Athena, and delivers interactive analytics through Power BI.

The project was built to demonstrate a complete modern analytics workflow from **API ingestion to cloud storage, data modeling, SQL analytics, data quality validation, and BI reporting**.

---

## Project Overview

Organizations often rely on public economic and social datasets to understand global development trends. However, raw API data is not immediately ready for analytical reporting.

This project builds a reusable pipeline that transforms World Bank Open Data into an analytics-ready cloud platform.

The pipeline processes indicators such as:

- GDP
- GDP per capita
- Population
- Life expectancy
- Internet usage
- Unemployment

The final analytical dataset supports country-level, regional, economic, demographic, and digital-development analysis.

---

## Business Objective

The main goal was to answer questions such as:

- How do development indicators vary across countries and regions?
- Which countries have the highest GDP per capita?
- How has economic development changed over time?
- Is GDP per capita associated with internet adoption?
- Is GDP per capita associated with life expectancy?
- Which countries have the highest unemployment rates?
- How complete is the available World Bank data across years and indicators?

The project also demonstrates how an analyst can move beyond downloading CSV files and instead build a **scalable cloud-based analytics pipeline**.

---

## Architecture

```mermaid
flowchart LR
    A[World Bank API] --> B[Python ETL]
    B --> C[Amazon S3 Raw JSON]
    C --> D[Data Cleaning & Transformation]
    D --> E[Amazon S3 Processed Parquet]
    E --> F[AWS Glue Data Catalog]
    F --> G[Amazon Athena]
    G --> H[Power BI]
```

### Pipeline Flow

```text
World Bank API
       ↓
Python
Extraction & Transformation
       ↓
Amazon S3
Raw JSON + Processed Parquet
       ↓
AWS Glue
Data Catalog
       ↓
Amazon Athena
SQL Analytics Layer
       ↓
Power BI
Interactive Dashboards
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Data Source | World Bank REST API |
| Programming | Python |
| API Requests | Requests |
| Data Processing | Pandas |
| AWS SDK | Boto3 |
| Cloud Storage | Amazon S3 |
| File Format | JSON / Parquet |
| Metadata Catalog | AWS Glue Data Catalog |
| SQL Query Engine | Amazon Athena |
| Data Modeling | Star Schema |
| Visualization | Microsoft Power BI |
| Version Control | Git / GitHub |

---

## Dataset

The project collects World Bank development indicators for approximately **217 countries and territories** across the period **2020–2025**.

The six primary indicators are:

| Indicator | World Bank Code |
|---|---|
| GDP | `NY.GDP.MKTP.CD` |
| GDP per Capita | `NY.GDP.PCAP.CD` |
| Population | `SP.POP.TOTL` |
| Life Expectancy | `SP.DYN.LE00.IN` |
| Internet Usage | `IT.NET.USER.ZS` |
| Unemployment | `SL.UEM.TOTL.ZS` |

Country metadata such as region and income level is also retrieved from the World Bank Country API.

---

## Project Workflow

### 1. API Data Extraction

Python scripts send requests to the World Bank REST API for each configured indicator.

The extraction layer:

- loops through multiple indicators
- requests observations from 2020–2025
- handles API errors
- stores raw responses
- uploads the source data to Amazon S3

Raw data is preserved so the pipeline can be reprocessed without calling the API again.

---

### 2. Raw Data Storage

Original API responses are stored in Amazon S3 as JSON.

Example logical structure:

```text
raw/
└── indicators/
    ├── gdp/
    ├── gdp_per_capita/
    ├── population/
    ├── life_expectancy/
    ├── internet_usage/
    └── unemployment/
```

Keeping raw data provides:

- traceability
- reproducibility
- easier debugging
- protection against source/API changes

---

## 3. Data Transformation

Pandas is used to convert nested World Bank API responses into structured analytical datasets.

The transformation layer performs:

- JSON flattening
- data-type conversion
- null validation
- duplicate removal
- aggregate-entity filtering
- country validation
- indicator standardization

World Bank aggregate entities are removed so regional totals are not incorrectly treated as individual countries.

---

## 4. Processed Parquet Layer

Clean analytical datasets are stored in Amazon S3 as **Parquet** files.

Parquet was selected because it provides:

- columnar storage
- compression
- faster analytical queries
- lower Athena data-scanning requirements
- better cloud analytics performance than raw JSON

The processed layer contains both dimensions and fact datasets.

---

## Data Model

The project uses a simple star schema.

```text
              dim_country
                  |
                  |
                  |
dim_indicator — fact_indicators
```

### `dim_country`

Contains descriptive country attributes:

```text
country_code
country_name
region
income_level
```

### `dim_indicator`

Contains indicator metadata:

```text
indicator_code
indicator_name
short_name
category
```

### `fact_indicators`

Contains numerical observations.

Grain:

> One row per country, indicator, and year.

Columns:

```text
country_code
indicator_code
year
value
```

---

## 5. AWS Glue Data Catalog

AWS Glue provides the metadata layer between the S3 files and Athena.

Glue stores information about:

- databases
- tables
- schemas
- columns
- file locations

The actual analytical data remains stored in Amazon S3.

---

## 6. Amazon Athena Analytics Layer

Amazon Athena is used as the serverless SQL analytics engine.

Athena queries the Parquet files stored in S3 using metadata registered in the Glue Data Catalog.

The project includes several analytical views.

### Country Indicator View

Combines fact observations with country and indicator metadata.

```text
vw_country_indicators
```

### Latest Country Indicators

Returns the most recent available value for each country and indicator.

```text
vw_latest_country_indicators
```

### Regional Indicator Summary

Provides regional averages, minimums, maximums, and observation counts.

```text
vw_regional_indicator_summary
```

### Country-Year Metrics

Pivots development indicators into one row per country and year.

```text
vw_country_year_metrics
```

This view supports cross-indicator analysis such as:

- GDP per capita vs internet adoption
- GDP per capita vs life expectancy
- unemployment comparisons

---

## Power BI Dashboard

The final Power BI report contains three analytical pages.

### Page 1 — Global Development Overview

Provides a high-level development snapshot.

Includes:

- GDP
- GDP per capita
- population
- life expectancy
- historical trends
- regional comparisons
- country rankings

---

### Page 2 — Economic & Digital Analysis

Explores relationships between economic and social indicators.

Includes:

- GDP per capita vs internet adoption scatter plot
- GDP per capita vs life expectancy scatter plot
- GDP–internet correlation
- highest unemployment rates
- internet adoption rankings
- region and income-level filtering

This page allows users to investigate relationships between economic prosperity, digital connectivity, and quality of life.

---

### Page 3 — Cloud Pipeline & Data Quality

Explains the engineering architecture and dataset reliability.

Includes:

- total countries
- total indicators
- total observations
- latest data year
- observed data coverage
- observations by year
- observations by indicator
- cloud architecture
- data-quality rules

---

## Dashboard Screenshots

### Executive Overview

![Overview Dashboard](dashboard/screenshots/overview.png)

### Economic & Digital Analysis

![Economic and Digital Analysis](dashboard/screenshots/economic-digital-analysis.png)

### Cloud Pipeline & Data Quality

![Cloud Pipeline and Data Quality](dashboard/screenshots/cloud-pipeline-quality.png)

---

## Data Quality Rules

Several validation rules are applied during transformation.

- World Bank aggregate entities are excluded from country-level analysis.
- Duplicate country–indicator–year records are removed.
- Null indicator observations are excluded from the analytics fact table.
- Country codes are validated against the country dimension.
- Raw API responses are preserved for traceability.
- Processed datasets are stored in Parquet.
- Reporting coverage is monitored by country, year, and indicator.

---

## Repository Structure

```text
worldbank-aws-analytics-pipeline/
│
├── src/
│   ├── build_dim_indicator.py
│   ├── build_fact_indicators.py
│   ├── config.py
│   ├── extract_country_metadata.py
│   ├── extract_indicators.py
│   ├── extract_worldbank.py
│   ├── transform_country_metadata.py
│   └── transform_worldbank.py
│
├── sql/
│   ├── create_tables.sql
│   ├── create_views.sql
│   └── analysis_queries.sql
│
├── dashboard/
│   └── screenshots/
│       ├── overview.png
│       ├── economic-digital-analysis.png
│       └── cloud-pipeline-quality.png
│
├── docs/
│   ├── architecture.png
│   └── WorldBank_AWS_Cloud_Analytics_Interview_Report.pdf
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Running the Project

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/worldbank-aws-analytics-pipeline.git
```

```bash
cd worldbank-aws-analytics-pipeline
```

---

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages include:

```text
boto3
pandas
pyarrow
requests
```

---

### 3. Configure AWS Authentication

The scripts use the standard AWS credential chain or a local AWS CLI profile.

Example:

```bash
aws configure --profile worldbank-dev
```

AWS credentials should never be stored directly in the source code or committed to GitHub.

---

### 4. Extract Indicator Data

```bash
python src/extract_indicators.py
```

---

### 5. Extract Country Metadata

```bash
python src/extract_country_metadata.py
```

---

### 6. Transform the Data

Run the transformation scripts:

```bash
python src/transform_worldbank.py
```

```bash
python src/transform_country_metadata.py
```

---

### 7. Build Analytical Tables

```bash
python src/build_dim_indicator.py
```

```bash
python src/build_fact_indicators.py
```

---

### 8. Register Tables and Views in Athena

Run the SQL scripts located in:

```text
sql/
```

These create the external analytical tables and views used by Power BI.

---

## Key Engineering Decisions

### Why preserve raw JSON?

Raw data creates an immutable source layer that allows the pipeline to be reprocessed without calling the external API again.

### Why Parquet?

Parquet is column-oriented and compressed, making it more efficient for Athena analytical workloads.

### Why a star schema?

Separating facts from descriptive dimensions improves analytical consistency and makes the data easier to consume in SQL and Power BI.

### Why AWS Glue?

Glue provides a central metadata catalog that Athena can use to understand the structure and location of datasets stored in S3.

### Why Athena?

Athena provides serverless SQL analytics without requiring a dedicated database server.

### Why Power BI?

Power BI provides the semantic and visualization layer required for interactive business analysis.

---

## Challenges & Solutions

### AWS Permission Management

IAM permissions were implemented using least-privilege access instead of broad administrator permissions.

The pipeline user was granted only the S3, Glue, and Athena permissions required for the project.

### Athena Query Result Permissions

Athena requires write permissions to an S3 query-results location. Appropriate access was added specifically for the Athena results prefix.

### World Bank Aggregate Records

The World Bank Country API contains aggregate entities that could otherwise be mistaken for individual countries.

The country dimension is used as the trusted list of valid country codes.

### Duplicate and Missing Observations

The transformation layer validates country–indicator–year grain, removes duplicates, and excludes null observations.

### Power BI Scatter Plot Aggregation

Power BI initially aggregated all countries into a single scatter point.

The issue was resolved by using country name as the observation grouping field and using averages for GDP per capita and internet usage.

---

## Project Outcomes

The project successfully demonstrates:

- API ingestion with Python
- AWS authentication and IAM
- cloud data-lake design
- raw and processed data layers
- JSON-to-Parquet transformation
- dimensional data modeling
- AWS Glue metadata management
- serverless SQL analytics with Athena
- data-quality validation
- analytical SQL views
- Power BI semantic modeling
- DAX measures
- interactive dashboard development

The final result is an end-to-end analytics solution that transforms public API data into business-ready insights using a modern cloud architecture.

---

## Future Improvements

Potential extensions include:

- AWS Lambda for serverless execution
- Amazon EventBridge for scheduled ingestion
- CloudWatch logging and monitoring
- incremental data loading
- automated data-quality tests
- infrastructure-as-code
- CI/CD with GitHub Actions
- S3 lifecycle policies
- additional World Bank indicators
- automated Power BI dataset refresh

---

## Documentation

Additional technical and interview-preparation documentation is available in:

```text
docs/WorldBank_AWS_Cloud_Analytics_Interview_Report.pdf
```

---

## Author

**Rudra Patel**

Data Analytics | Business Intelligence | Data Engineering

Canada