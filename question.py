from vertexai.generative_models import GenerationConfig, HarmBlockThreshold, HarmCategory
from google.cloud import aiplatform_v1
import re
import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig


def generate_text(model_gemini, model_embedding, question) -> str:
    def generate_text1(project_id: str, location: str, prompt) -> str:
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        # Load the model
        multimodal_model = GenerativeModel(model_name="gemini-1.5-flash")
        # Query the model
    
        config = GenerationConfig(
        max_output_tokens=4096, temperature=0.8, top_p=0, top_k=5, candidate_count=1)
        response = multimodal_model.generate_content([prompt], generation_config=config)
        return response.text
    
    gen_kab = """
jika ada, tuliskan nama kabupaten di Indonesia dari teks di bawah ini berikan jawaban yang to the point tanpa tanda baca:         
'"""+question+"""'
Jika tidak menemukannya tuliskan 'tidak ada nama kabupaten'
"""
    kabupaten = generate_text1(project_id='ai4indonesia',location='asia-southeast1', \
              prompt=gen_kab
            )

    gen_kec = """
jika ada, apakah nama kecamatan di Indonesia dari teks di bawah ini? berikan jawaban yang to the point tanpa tanda baca:         
'"""+question+"""'
Jika tidak menemukannya tuliskan 'tidak ada nama kecamatan'
"""
    kecamatan = generate_text1(project_id='ai4indonesia',location='asia-southeast1', \
              prompt=gen_kec
            )
    kabupaten = kabupaten.strip()
    kecamatan = kecamatan.strip()

    test_embeddings = model_embedding.get_embeddings([question])

    # SET Vector Database
    API_ENDPOINT = "96971642.asia-southeast2-225811511996.vdb.vertexai.goog"
    INDEX_ENDPOINT = "projects/225811511996/locations/asia-southeast2/indexEndpoints/5456392423536066560"
    DEPLOYED_INDEX_ID ="test_1722174236342"

    # Configure Vector Search client
    client_options = {
      "api_endpoint": API_ENDPOINT
    }
    vector_search_client = aiplatform_v1.MatchServiceClient(
      client_options=client_options)

    # Build FindNeighborsRequest object
    datapoint = aiplatform_v1.IndexDatapoint(feature_vector=test_embeddings[0].values)

    query = aiplatform_v1.FindNeighborsRequest.Query(datapoint=datapoint, neighbor_count=50)
    request = aiplatform_v1.FindNeighborsRequest(index_endpoint=INDEX_ENDPOINT,
                                                 deployed_index_id=DEPLOYED_INDEX_ID,
                                                 queries=[query],
                                                 return_full_datapoint=False)

    # Execute the request
    response = vector_search_client.find_neighbors(request)

    # Handle the response
    text = ""
    text1=""
    for x in response.nearest_neighbors[0].neighbors:
        #print(x.datapoint.datapoint_id)
        if kecamatan == kabupaten and kabupaten.lower() != "tidak ada nama kabupaten":
            if kabupaten.lower() in x.datapoint.datapoint_id.lower():
                #print(1)
                text = text + \
            """
            ---
    
            """ + x.datapoint.datapoint_id
        elif kabupaten.lower() == "tidak ada nama kabupaten" and kecamatan == "tidak ada nama kecamatan":
            text = text + \
            """
            ---
    
            """ + x.datapoint.datapoint_id
        elif kabupaten.lower() == "tidak ada nama kabupaten" and kecamatan != "":
            if kecamatan.lower() in x.datapoint.datapoint_id.lower():
                #print(2)
                text = text + \
            """
            ---
    
            """ + x.datapoint.datapoint_id
        elif kecamatan.lower() == "tidak ada nama kecamatan" and kabupaten != "":
            if kabupaten.lower() in x.datapoint.datapoint_id.lower():
            #print(3)
                text = text + \
            """
            ---
    
            """ + x.datapoint.datapoint_id
        else:
        #print(4)
            text = text + \
            """
            ---
    
            """ + x.datapoint.datapoint_id

    if kecamatan == "tidak ada nama kecamatan":
        kecamatan1 = ""
    else:
        kecamatan1 = " for kecamatan "+kecamatan

    if kabupaten == "tidak ada nama kabupaten":
        kabupaten1 = ""
    else:
        kabupaten1 = " or kabupaten "+kabupaten
    

    prompt = """
    Answer the question based only on the following context:
    """+text+\
    """
    ---
    
    Answer the question based on the above context without mentioning any "context" word, give a brief reason, compare the number if needed, compare the growth if needed, put any percentation if needed, be very detail, humanize the answer and in Bahasa Indonesia: """+question+\
    """
    put a bold markdown on every Kecamatan or Kabupaten Name.
    """

    
    # Load the model
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH}

    config = GenerationConfig(max_output_tokens=4096, temperature=0.8, top_p=0, top_k=1, candidate_count=1)
    response = model_gemini.generate_content([prompt], generation_config=config, safety_settings=safety_settings,)
    
    
    return response.text

