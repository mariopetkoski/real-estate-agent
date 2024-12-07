FROM apache/airflow:2.10.2

# Install additional packages
RUN pip install --no-cache-dir pandas requests tqdm beautifulsoup4 psycopg2-binary langchain langchain_community langchain-openai
