import functions_framework
from question_api import generate_text
import logging
from insert_big_query import insert_data_to_bq
import threading
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "ai4indonesia"
LOCATION = "asia-southeast1"
BQ_TABLE = "geoplan_log"
BQ_DATASET = "geoplan_dev"

def load_models():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model_gecko = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
    model_gen = GenerativeModel(model_name="gemini-1.5-flash")
    return model_gen, model_gecko


model_gemini, model_embedding = load_models()


@functions_framework.http
def make_call(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    logging.info(f"request_json : {type(request_json)}")
    logging.info(f"request_args : {type(request_args)}")

    # checking the question if available.
    try:
        if request_json is None and request_args is None:
            return "Mohon berikan pertanyaan"
        else:
            if 'question' not in request_json and 'question' not in request_args:
                return "Mohon berikan pertanyaan"
            else:
                question = request_json.get('question') or request_args.get('question')

        response = generate_text(model_gemini, model_embedding, question)
        data_to_bq = {'user_query': question,
                      'llm_answer': response,
                      'dataset_id': BQ_DATASET,
                      "table_id": BQ_TABLE,
                      'location': LOCATION}

        thread = threading.Thread(target=insert_data_to_bq, kwargs=data_to_bq)
        thread.start()

        return response

    except Exception as err:
        return f"{err}"


