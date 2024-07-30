from google.cloud import bigquery
from datetime import datetime
import pytz
import uuid
import logging


def insert_data_to_bq(user_query, llm_answer, dataset_id, table_id, location):
    date_now = datetime.now(pytz.timezone("Asia/Jakarta"))
    client = bigquery.Client(location=location)
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)

    data = {'query_id': str(uuid.uuid4()),
            'user_query': user_query,
            'llm_answer': llm_answer,
            'timestamp': f"{date_now}"}

    # Insert the data into the BigQuery table
    errors = client.insert_rows_json(table, [data])
    if errors:
        logging.info('Encountered errors while inserting data:', errors)
    else:
        logging.info('Data inserted successfully.')
