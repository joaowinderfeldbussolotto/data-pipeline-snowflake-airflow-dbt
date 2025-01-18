from typing import Dict, List, Any, Annotated, Literal, Optional
import logging
import json
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage, AnyMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, START
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from prompts import Prompts
from utils import llm_call, get_model_name

logger = logging.getLogger(__name__)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    sql_query: Optional[str] = None
    execution_result: Optional[str] = None
    error: Optional[str] = None

def handle_tool_error(state) -> dict:
    """Handle errors from tool execution."""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> RunnableWithFallbacks:
    """Create a ToolNode with error handling."""
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], 
        exception_key="error"
    )

def log_llm_message(message: Any, step: str) -> None:
    """Log LLM message content with pretty formatting.""" 
    logger.info(f"\n{'='*50}\nLLM {step} Output:\n{'-'*50}")
    
    if hasattr(message, 'content') and message.content:
        logger.info(f"Content: {message.content}")
    
    if hasattr(message, 'tool_calls') and message.tool_calls:
        logger.info(f"Tool Calls: {json.dumps(message.tool_calls, indent=2)}")
    
    logger.info(f"{'='*50}\n")

class WorkflowNodes:
    def __init__(self, llm_query_gen, llm_query_check, llm_answer, db_manager, tools):
        """Initialize with different LLMs for each task."""
        self.llm_query_gen = llm_query_gen  # Codestral for query generation
        self.llm_query_check = llm_query_check  # Llama for query validation
        self.llm_answer = llm_answer  # Mixtral for answer generation
        self.db_manager = db_manager
        self.tools = tools

    def first_tool_call(self, state: State) -> Dict[str, List[AIMessage]]:
        """Initial node to list available tables."""
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "sql_db_list_tables",
                        "args": {},
                        "id": "tool_initial",
                    }]
                )
            ]
        }

    @llm_call
    def model_get_schema(self, state: Dict) -> Dict[str, List[AIMessage]]:
        """Get schema for relevant tables."""
        logger.info("Getting schema information")
        schema_getter = self.llm_query_gen.bind_tools([self.tools["get_schema"]])
        # Pass messages list directly
        result = schema_getter.invoke(state["messages"])
        log_llm_message(result, "Schema Analysis")
        return {"messages": [result]}


    @llm_call
    def query_gen_node(self, state: State) -> Dict:
        """Generate SQL query using Codestral."""
        logger.info(f"Generating SQL query with {get_model_name(self.llm_query_gen)}")
        messages = state["messages"]
        if state.get("error"):
            messages = messages + [HumanMessage(content=f"Previous error: {state['error']}. Please fix the query.")]
        
        query_gen = Prompts.QUERY_GEN | self.llm_query_gen
        result = query_gen.invoke(messages)
        log_llm_message(result, "Query Generation (Codestral)")
        
        # Extract SQL from message content
        if result.content and "```sql" in result.content:
            sql = result.content.split("```sql")[1].split("```")[0].strip()
            return {
                "messages": state["messages"] + [result],
                "sql_query": sql,
                "error": None
            }
        
        return {
            "messages": state["messages"] + [result],
            "error": "No SQL query generated"
        }

    @llm_call
    def query_check_node(self, state: State) -> Dict:
        """Validate SQL query using Llama."""
        logger.info(f"Validating SQL query with {get_model_name(self.llm_query_check)}")
        query_check = Prompts.QUERY_CHECK | self.llm_query_check
        messages = [
            SystemMessage(content="Validate this SQL query:"),
            HumanMessage(content=state["sql_query"])
        ]
        
        result = query_check.invoke(messages)
        log_llm_message(result, "Query Validation (Llama)")
        
        if "```sql" in result.content:
            validated_sql = result.content.split("```sql")[1].split("```")[0].strip()
            return {
                "messages": state["messages"] + [result],
                "sql_query": validated_sql,
                "error": None
            }
        
        return {
            "messages": state["messages"] + [result],
            "error": "Query validation failed"
        }

    @llm_call
    def generate_answer_node(self, state: State) -> Dict:
        """Generate final answer using Mixtral."""
        logger.info(f"Generating answer with {get_model_name(self.llm_answer)}")

        if state.get('error'):
            return {
                "messages": state["messages"],
                "error": state["error"]
            }
        
   
        
        # submit_answer = self.llm_answer.bind_tools([SubmitFinalAnswer])
        final_message = self.llm_answer.invoke([
            SystemMessage(content="Generate a clear answer based on the SQL results. Make sure the answer is in the language of the user query."),
            HumanMessage(content=f"Query: {state['sql_query']}\nResults: {state['execution_result']}")
        ])

        
        return {
            "messages": state["messages"] + [final_message],
            "error": None
        }

    def execute_query_wrapper(self, state: State) -> Dict:
        """Execute query and store results in state."""
        if not state.get("sql_query"):
            return {
                "messages": state["messages"],
                "error": "No SQL query to execute"
            }
        
        try:
            logger.info(f"Executing query: {state['sql_query']}")
            result = self.tools["execute_query"](state["sql_query"])

            if result.startswith("Error"):
                raise Exception(result)
        
            return {
                "messages": state["messages"] + [
                    AIMessage(content=f"Query executed successfully:\n{result}")
                ],
                "execution_result": result,
                "error": None
            }
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return {
                "messages": state["messages"],
                "error": f"Query execution failed: {str(e)}"
            }

class WorkflowBuilder:
    def __init__(self, llm_query_gen, llm_query_check, llm_answer, db_manager, tools):
        self.llm_query_gen = llm_query_gen
        self.llm_query_check = llm_query_check
        self.llm_answer = llm_answer
        self.db_manager = db_manager
        self.tools = tools
        self.nodes = WorkflowNodes(llm_query_gen, llm_query_check, llm_answer, db_manager, tools)
        self.workflow = StateGraph(State)
        self._build_workflow()

    def _build_workflow(self):
        # Add nodes
        self.workflow.add_node("first_tool_call", self.nodes.first_tool_call)
        self.workflow.add_node("list_tables_tool", 
                             create_tool_node_with_fallback([self.tools["list_tables"]]))
        self.workflow.add_node("get_schema_tool", 
                             create_tool_node_with_fallback([self.tools["get_schema"]]))
        self.workflow.add_node("model_get_schema", self.nodes.model_get_schema)
        self.workflow.add_node("query_gen", self.nodes.query_gen_node)
        self.workflow.add_node("query_check", self.nodes.query_check_node)
        self.workflow.add_node("execute_query", self.nodes.execute_query_wrapper)
        self.workflow.add_node("generate_answer", self.nodes.generate_answer_node)

        # Define conditional edge only for answer evaluation
        def should_retry_or_end(state: State) -> Literal["query_gen", END]:
            """Only used after answer generation to decide if we need to retry"""
            if state.get("error") or not state.get("execution_result"):
                return "query_gen"  # Retry if error or no results
            return END

        # Define linear flow
        self.workflow.add_edge(START, "first_tool_call")
        self.workflow.add_edge("first_tool_call", "list_tables_tool")
        self.workflow.add_edge("list_tables_tool", "model_get_schema")
        self.workflow.add_edge("model_get_schema", "get_schema_tool")
        self.workflow.add_edge("get_schema_tool", "query_gen")
        self.workflow.add_edge("query_gen", "query_check")
        self.workflow.add_edge("query_check", "execute_query")
        self.workflow.add_edge("execute_query", "generate_answer")
        
        # Only conditional edge is after answer generation
        self.workflow.add_conditional_edges("generate_answer", should_retry_or_end)

    def compile(self):
        return self.workflow.compile()

def create_workflow(llm_query_gen, llm_query_check, llm_answer, db_manager, tools):
    """Factory function to create and compile the workflow."""
    workflow_builder = WorkflowBuilder(llm_query_gen, llm_query_check, llm_answer, db_manager, tools)
    return workflow_builder.compile()