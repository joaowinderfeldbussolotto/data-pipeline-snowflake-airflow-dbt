from typing import Annotated, Literal
from langchain_core.tools import tool
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict
from database_manager import DatabaseManager
from llm_factory import LLMFactory
from config import settings
from workflow_nodes import create_workflow as create_workflow_graph

db_manager = DatabaseManager(settings.database.connection_url)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def create_workflow():
    # Create different LLMs for each task
    llm_query_gen = LLMFactory.create(
        provider="mistral",
        model="codestral-latest",
        temperature=0,
        max_retries=4
    )
    
    llm_query_check = LLMFactory.create(
        provider="groq",
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_retries=4
    )
    
    llm_answer = LLMFactory.create(
        provider="groq",
        model="llama-3.1-70b-versatile",
        temperature=0,
        max_retries=4
    )



    # Initialize toolkit with query generation LLM
    toolkit = db_manager.create_toolkit(llm_query_gen)
    tools = toolkit.get_tools()

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")

    @tool
    def db_query_tool(query: str) -> str:
        """
        Execute a SQL query against the database and return the results.
        If the query is not correct, an error message will be returned.
        If an error is returned, rewrite the query and try again.
        """
        return db_manager.execute_query(query)

    return create_workflow_graph(
        llm_query_gen=llm_query_gen,
        llm_query_check=llm_query_check,
        llm_answer=llm_answer,
        db_manager=db_manager,
        tools={
            "list_tables": list_tables_tool,
            "get_schema": get_schema_tool,
            "execute_query": db_query_tool
        }
    )

def main():
    agent = create_workflow()
    question = "As 5 concessionárias que mais vendem, e de que estado são?"
    
    print("\nPERGUNTA:")
    print("="*80)
    print(question)
    print("="*80)
    
    state = agent.invoke({
        "messages": [("user", question)]
    })
    
    print("\nSTATE FINAL:")
    print("="*80)
    print(state)
    print("="*80)
    
    if state.get("sql_query"):
        print("\nSQL GERADO:")
        print("="*80)
        print(state["sql_query"])
        print("="*80)
    
    if state.get("execution_result"):
        print("\nRESULTADO DO SQL (TABELA):")
        print("="*80)
        print(state["execution_result"])
        print("="*80)
    
    final_answer = state.get("messages")[-1].content
    if final_answer:
        print("\nRESULTADO FINAL:")
        print("="*80)
        print(final_answer)
        print("="*80)

    if state.get("error"):
        print("\nERRO:")
        print("="*80)
        print(state["error"])
        print("="*80)

if __name__ == "__main__":
    main()