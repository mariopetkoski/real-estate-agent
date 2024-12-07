import os
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_aws import ChatBedrock

# Set up the OpenAI API key
key = os.environ.get('OPENAI_API_KEY')

# Create the database and LLM agent
db = SQLDatabase.from_uri("postgresql://airflow:airflow@postgres:5432/properties")
# llm = ChatBedrock(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", model_kwargs=dict(temperature=0),)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=key)
# llm_llama = ChatBedrock(model_id="llama", model_kwargs=dict(temperature=0),)
# llm_claude = ChatBedrock(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", model_kwargs=dict(temperature=0),)

custom_prefix = """You are an agent that helps users make queries from a SQL database.
    For each query, you MUST provide your response in the following format:

    SQL Query:
    <show the exact SQL query>

    DataFrame:
    <show the results in a formatted table>

    Analysis:
    <provide a clear text explanation of the findings>

    Remember to ALWAYS follow this format for every response.
    """

agent_executor = create_sql_agent(llm, db=db, verbose=True, agent_type="openai-tools", prefix=custom_prefix)

# Initialize session state for storing history
if 'history' not in st.session_state:
    st.session_state.history = []

# Streamlit layout adjustments
st.set_page_config(page_title="Property Query Agent", layout="centered")  # Center the layout
st.title("🏡 Real Estate AI Agent")
st.subheader("🔍 Ask questions about properties in the database:")

# Create a form to accept user queries
with st.form(key="query_form"):
    question = st.text_input("💬 Enter your query", "Give me top 3 properties with 3 bedrooms under 100000 EUR")
    submit_button = st.form_submit_button(label="🆗 Submit")

if submit_button:
    # Execute the agent's query
    with st.spinner("Fetching data..."):
        try:
            answer = agent_executor.invoke(question)
            st.success("✅ Query completed successfully!")

            # Add the question and answer to history
            st.session_state.history.append({"question": question, "answer": answer["output"]})
            # TODO: Extract sql query
            # Display the results
            st.write("**Answer:**")
            st.write(answer["output"])
            # st.write(answer)
        except Exception as e:
            st.error(f"🚨 An error occurred: {e}")

# Display the history of questions and answers
st.subheader("📝 Query History")

# Format and display history
for idx, item in enumerate(st.session_state.history, start=1):
    # Container for Question
    with st.container():
        st.markdown(
            f"<div style='background-color: #f0f8ff; padding: 10px; border-radius: 5px;'><strong>Query {idx}:</strong> {item['question']}</div>",
            unsafe_allow_html=True
        )

    # Container for Answer
    with st.container():
        st.markdown(
            f"<div style='background-color: #e6ffe6; padding: 10px; border-radius: 5px;'><strong>Answer:</strong> {item['answer']}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)  # Add a horizontal line between entries

