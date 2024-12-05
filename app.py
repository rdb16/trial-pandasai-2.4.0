import json
import streamlit as st
import pandas as pd
from PIL import Image
import boto3
from pandasai import SmartDataframe
from pandasai.schemas.df_config import Config
from utils.pdf_utils import create_kai_pdf
from utils.get_aws_llm import get_aws_llm

# Configuration de la page
st.set_page_config(page_title="SNTP Capitalisation", page_icon="\U0001F4B0", layout="centered")

# Initialiser session_state pour session_data et les indicateurs de questions ajoutées
if 'session_data' not in st.session_state:
    st.session_state.session_data = []

if 'added_overview' not in st.session_state:
    st.session_state.added_overview = False

if 'added_summary' not in st.session_state:
    st.session_state.added_summary = False

if 'show_new_question_button' not in st.session_state:
    st.session_state.show_new_question_button = False

if 'show_envoyer_button' not in st.session_state:
    st.session_state.show_envoyer_button = True

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# Initialiser `sdf`, `nb_ln`, `nb_c` et `column_names` dans `session_state` s'ils n'existent pas
if 'sdf' not in st.session_state:
    st.session_state.sdf = None

if 'nb_ln' not in st.session_state:
    st.session_state.nb_ln = None

if 'nb_c' not in st.session_state:
    st.session_state.nb_c = None

if 'column_names' not in st.session_state:
    st.session_state.column_names = None

# read configuration
@st.cache_resource
def read_conf():
    with open('general_config.json', 'r') as f:
        return json.load(f)


@st.cache_resource
def get_css_style():
    with open("assets/styles/style.css", "r") as f:
        return f.read()


@st.cache_resource
def get_logo():
    logo = Image.open("assets/logo/sntpk-ia-logo.jpeg")
    return logo


config = read_conf()
llm = get_aws_llm(config)
if llm is None:
    st.warning("No AWS LLM detected")

st.markdown(f"<style>{get_css_style()}</style>", unsafe_allow_html=True)
st.image(get_logo(), width=100, caption=None)
st.markdown("""
    <div class="title">
        POC PandasAI <br> avec Bedrock claude 3.0 
    </div>
    <div class="footer">
        &copy; 2024-2025 SNTP Capitalisation. Tous droits réservés.
    </div>
""", unsafe_allow_html=True)

# on charge le dataset
if st.session_state.sdf is None:
    uploaded_file = st.file_uploader("Choisissez un fichier (CSV, XLS, XLSX)", type=["csv", "xls", "xlsx"])
    st.session_state.session_data.append('data_set')

    if uploaded_file is not None:
        data = None
        if uploaded_file.name.split('.')[-1] == 'csv':
            data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.split('.')[-1] == 'xlsx':
            data = pd.read_excel(uploaded_file)
        elif uploaded_file.name.split('.')[-1] == 'xls':
            data = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type")

        sdf_cfg = Config(
            llm=llm,
            model=config['aws_model'],
            max_tokens=config['llm_max_tokens'],
            temperature=config['llm_temperature']
        )
        if sdf_cfg is None:
            st.warning("No AWS LLM detected")

        sdf = SmartDataframe(data, config=sdf_cfg)
        st.session_state.sdf = sdf
        nb_ln, nb_c = data.shape
        st.session_state.nb_ln = nb_ln
        st.session_state.nb_c = nb_c
        st.session_state.column_names = list(data.columns)



# affichage des infos sur le datasae
if st.session_state.sdf is not None:
    st.write(f"Dataset dimensions : lines : {st.session_state.nb_ln}, columns : {st.session_state.nb_c}")
    st.write(f"Nom des colonnes :")
    st.write(f" {', '.join(st.session_state.column_names)}")

if st.session_state.columns_description is not None: