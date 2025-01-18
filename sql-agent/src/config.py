from pathlib import Path
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables from a .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    account: str
    user: str
    password: str
    database: str
    schema: str
    warehouse: str
    role: str

    @property
    def connection_url(self) -> str:
        return (
            f"snowflake://{self.user}:{self.password}@{self.account}/"
            f"{self.database}/{self.schema}?"
            f"warehouse={self.warehouse}&"
            f"role={self.role}"
        )

@dataclass
class Settings:
    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_warehouse: str
    snowflake_role: str

    mistral_api_key: str
    groq_api_key: str
    llm_provider: str = "mistral"
    llm_model: Optional[str] = None

    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            account=self.snowflake_account,
            user=self.snowflake_user,
            password=self.snowflake_password,
            database=self.snowflake_database,
            schema=self.snowflake_schema,
            warehouse=self.snowflake_warehouse,
            role=self.snowflake_role
        )

settings = Settings(
    snowflake_account=os.getenv("SNOWFLAKE_ACCOUNT"),
    snowflake_user=os.getenv("SNOWFLAKE_USER"),
    snowflake_password=os.getenv("SNOWFLAKE_PASSWORD"),
    snowflake_database=os.getenv("SNOWFLAKE_DATABASE"),
    snowflake_schema=os.getenv("SNOWFLAKE_SCHEMA"),
    snowflake_warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    snowflake_role=os.getenv("SNOWFLAKE_ROLE"),
    mistral_api_key=os.getenv("MISTRAL_API_KEY"),
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

