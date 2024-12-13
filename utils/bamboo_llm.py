import streamlit
from pandasai.llm import BambooLLM
from api_keys import PANDASAI_API_KEY


@streamlit.cache_resource
def get_bamboo_llm():
    _llm = BambooLLM(api_key=PANDASAI_API_KEY)
    return _llm

