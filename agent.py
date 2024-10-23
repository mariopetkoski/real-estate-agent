import os
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent

# Set up the OpenAI API key
key = os.environ.get('OPENAI_API_KEY')

# Create the database and LLM agent
db = SQLDatabase.from_uri("postgresql://airflow:airflow@localhost:5432/properties")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=key)
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

# Initialize session state for storing history
if 'history' not in st.session_state:
    st.session_state.history = []

# Streamlit layout adjustments
st.set_page_config(page_title="Property Query Agent", layout="centered")  # Center the layout
st.title("🏡 Real Estate AI Agent")
st.subheader("🔍 Ask questions about properties in the database:")

# Create a form to accept user queries
with st.form(key="query_form"):
    question = st.text_input("💬 Enter your query", "In which 3 location there are the most properties?")
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
