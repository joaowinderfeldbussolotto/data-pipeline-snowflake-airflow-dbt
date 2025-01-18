import streamlit as st
import pandas as pd
from agent import create_workflow
import re

def extract_sql(content: str) -> str:
    """Extract SQL query from message content."""
    if not content or 'SELECT' not in content.upper():
        return None

    if '```' in content:
        sql = content.split('```')[1]
        return sql.replace('sql\n', '').strip()
    
    query_start = content.upper().find('SELECT')
    query_end = content.find(';', query_start)
    if query_end == -1:
        return content[query_start:].strip()
    return content[query_start:query_end+1].strip()

def convert_to_dataframe(table_str: str) -> pd.DataFrame:
    """Convert ASCII table string to pandas DataFrame."""
    if not table_str or '|' not in table_str:
        return None
    
    lines = [line.strip() for line in table_str.split('\n') if line.strip()]
    headers = [col.strip() for col in lines[0].split('|')[1:-1]]
    
    data = []
    for line in lines[2:]:
        if '|' in line:
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            data.append(row)
    
    return pd.DataFrame(data, columns=headers)

def set_page_style():
    """Set custom page styling."""
    st.set_page_config(
        page_title="SQL Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stTextArea textarea {
            font-size: 1.1rem;
            border-radius: 0.5rem;
        }
        .stButton button {
            width: 100%;
            padding: 0.5rem;
            font-size: 1.1rem;
            border-radius: 0.5rem;
            background-color: #4CAF50;
            color: white;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        div[data-testid="stExpander"] {
            border: none;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .sql-code {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .results-table {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    set_page_style()
    
    # Header
    st.title("🤖 SQL Agent")
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <p style='font-size: 1.2rem; color: #666;'>
                Faça perguntas em linguagem natural e obtenha consultas SQL automaticamente
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input area with custom styling
    with st.form("query_form", clear_on_submit=False):
        question = st.text_area(
            "💭 Digite sua pergunta:",
            height=120,
            placeholder="Ex: Qual é o perfil dos clientes que compram carros mais caros? Qual é o valor que o carro foi vendido? Em quais regiões eles estão concentrados?",
            help="Faça perguntas claras e específicas para obter melhores resultados"
        )
        
        cols = st.columns([3, 1])
        with cols[1]:
            submitted = st.form_submit_button(
                "🔍 Consultar",
                use_container_width=True,
                type="primary"
            )
    
    if submitted and question:
        with st.spinner("🤔 Analisando sua pergunta..."):
            try:
                # Create and run workflow
                agent = create_workflow()
                state = agent.invoke({
                    "messages": [("user", question)]
                })
                
                # Create two tabs instead of three
                tab_answer, tab_details = st.tabs([
                    "✨ Resposta",
                    "🔍 Detalhes da Consulta"
                ])
                
                # Tab 1: Answer
                with tab_answer:
                    if state["messages"][-1].content:
                        st.info(state["messages"][-1].content)
                
                # Tab 2: SQL and Results
                with tab_details:
                    if state.get("sql_query"):
                        st.subheader("SQL Gerado:")
                        st.code(state["sql_query"], language='sql')
                        
                        if state.get("execution_result"):
                            st.subheader("Resultados:")
                            df = convert_to_dataframe(state["execution_result"])
                            if df is not None:
                                st.dataframe(
                                    df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        col: st.column_config.NumberColumn(
                                            col,
                                            format="%.2f"
                                        ) for col in df.select_dtypes(include=['float64']).columns
                                    }
                                )
                            else:
                                st.code(state["execution_result"])
                
                # Show any errors
                if state.get("error"):
                    st.error(f"❌ Erro: {state['error']}")
                    
            except Exception as e:
                st.error(f"❌ Ocorreu um erro: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()