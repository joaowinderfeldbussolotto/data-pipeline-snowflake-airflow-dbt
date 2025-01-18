import logging
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Optional, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self._db: Optional[SQLDatabase] = None
        self._toolkit: Optional[SQLDatabaseToolkit] = None

    @property
    def db(self) -> SQLDatabase:
        if not self._db:
            self._db = SQLDatabase.from_uri(
                self.connection_url,
                sample_rows_in_table_info=0
            )
        return self._db

    def create_toolkit(self, llm: Any) -> SQLDatabaseToolkit:
        """Create SQLDatabaseToolkit with the provided LLM."""
        self._toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
        return self._toolkit

    @property
    def toolkit(self) -> SQLDatabaseToolkit:
        """Lazy initialization of SQLDatabaseToolkit."""
        if not self._toolkit:
            raise ValueError("Toolkit not initialized. Call create_toolkit with an LLM first.")
        return self._toolkit

    def execute_query(self, query: str) -> str:
        """Execute a SQL query and return the results."""
        
        logger.info(f"\n{'='*50}\nExecuting Query:\n{'-'*50}\n{query}\n{'-'*50}")
        result = self.db.run_no_throw(query)
        
        if not result:
            logger.warning("Query execution failed")
            return "Error: Query failed. Please rewrite your query and try again."
        
        logger.info(f"\nQuery Results:\n{'-'*50}\n{result}\n{'='*50}")
        return result

    def get_table_info(self) -> str:
        """Get information about all tables."""
        return self.db.get_table_info()

    def get_schema(self, table_name: str) -> str:
        """Get schema information for a specific table."""
        return self.db.get_table_info(table_name)