# Automotive Sales Data Pipeline

A complete data pipeline solution for automotive sales analytics, featuring incremental data loading from PostgreSQL to Snowflake using Airflow, with DBT transformations for analytical insights.

## Architecture Overview
![Architecture Diagram](./assets/architecture.png)

The project consists of three main components:

1. **Data Ingestion (Airflow)**
   - Incremental loading from PostgreSQL
   - Daily scheduled execution
   - Optimized for performance and cost

2. **Data Transformation (DBT)**
   - Staging views for initial cleaning
   - Dimensional modeling
   - Fact tables for transactions
   - Analysis models for business insights

3. **Data Warehouse (Snowflake)**
   - Stores raw and transformed data
   - Supports analytical queries
   - Maintains data lineage

## Project Structure

```
pipeline-snowflake-airflow-dbt/
├── airflow-dag/                # Airflow DAG implementation
│   ├── dag-postgres-to-snowflake-incremental.py
│   └── README.md
├── dbt/                       # DBT transformations
│   ├── models/
│   │   ├── stage/            # Staging views
│   │   ├── dimensions/       # Dimension tables
│   │   ├── facts/           # Fact tables
│   │   └── analysis/        # Analysis models
│   ├── tests/               # Data quality tests
│   └── README.md
└── assets/                   # Documentation assets
    ├── dag_execution.png
    └── data_lineage_dbt.png
```

## Data Flow

1. **Source (PostgreSQL)**
   - Automotive sales operational data
   - Seven core tables tracking business entities

2. **Ingestion (Airflow)**
   - Daily incremental loads
   - ID-based tracking
   - Optimized customer data loading

3. **Transformation (DBT)**
   - Standardized staging views
   - Dimensional modeling
   - Business logic implementation
   - Analytical aggregations

4. **Analysis (Snowflake Views)**
   - Sales performance metrics
   - Geographic analysis
   - Temporal trends
   - Product insights

## Key Features

- **Incremental Processing**
  - ID-based incremental loads
  - Efficient resource utilization
  - Cost-optimized customer data handling

- **Data Quality**
  - Custom price validation tests
  - Relationship integrity checks
  - Business rule validation

- **Analysis Models**
  - Sales by geography
  - Salesperson performance
  - Vehicle popularity
  - Temporal analysis

## Infrastructure

### AWS Deployment
- Airflow running on EC2 instance
- Docker-based deployment
- Installation script provided in `airflow-dag/install_airflow_ec2.sh`

## Documentation

- Detailed Airflow DAG documentation: [airflow-dag/README.md](airflow-dag/README.md)
- DBT transformation details: [dbt/README.md](dbt/README.md)

## Monitoring

- Airflow web interface for pipeline status
- DBT documentation for transformation lineage
- Snowflake query history for performance

## Contact

For questions or support, please contact:
[Your Contact Information]
