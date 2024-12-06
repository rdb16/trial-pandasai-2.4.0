import datetime
import json
import os

import streamlit as st
import pandas as pd
from PIL import Image
import boto3
from pandasai import SmartDataframe
from pandasai.schemas.df_config import Config
from pandasai.connectors import PandasConnector
from utils.pdf_utils import create_kai_pdf
from utils.get_aws_llm import get_aws_llm
from utils.match_descriptions_file import find_matching_description_file


# Fonction pour nettoyer le champ d'input
def clear_input():
    st.session_state.input_text = ""
    st.session_state.output_text = ""
    st.session_state.show_new_question_button = False
    st.session_state.show_envoyer_button = True


# Fonction pour traiter la question
def handle_question(sdf1):
    prompt1 = st.session_state.input_text.strip()
    if prompt1:
        with st.spinner(text='En attente de la réponse !!'):
            try:
                response = sdf1.chat(prompt1)
            except Exception as e:
                st.error(f"Erreur lors de l'appel au LLM : {e}")
                response = "Une erreur est survenue. Veuillez réessayer"

        st.session_state.output_text = response
        st.session_state.session_data.append({"question": prompt1, "answer": response})
        st.session_state.show_envoyer_button = False
        st.session_state.show_new_question_button = True


# Configuration de la page
st.set_page_config(page_title="SNTP Capitalisation", page_icon="\U0001F4B0", layout="centered")

# Initialiser session_state pour session_data et les indicateurs de questions ajoutées
if 'study_date' not in st.session_state:
    st.session_state.study_date = None

if 'selected_dataset_name' not in st.session_state:
    st.session_state.selected_dataset = None

if 'description_file_name' not in st.session_state:
    st.session_state.selected_dataset = None

if 'show_new_question_button' not in st.session_state:
    st.session_state.show_new_question_button = False

if 'show_envoyer_button' not in st.session_state:
    st.session_state.show_envoyer_button = True

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

if 'output_text' not in st.session_state:
    st.session_state.out_text = ""

if 'sdf' not in st.session_state:
    st.session_state.sdf = None

if 'nb_ln' not in st.session_state:
    st.session_state.nb_ln = None

if 'nb_c' not in st.session_state:
    st.session_state.nb_c = None

if 'column_names' not in st.session_state:
    st.session_state.column_names = None

if 'session_data' not in st.session_state:
    st.session_state.session_data = []


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
        Streamlit for PandasAI <br> on AWS Bedrock Claude 3.0 
    </div>
    <div class="footer">
        &copy; 2024-2025 SNTP Capitalisation. Tous droits réservés.
    </div>
""", unsafe_allow_html=True)

# on charge le dataset
if st.session_state.sdf is None:
    st.session_state.study_date = timestamp = datetime.datetime.now().strftime("%m-%d-%Y  %H:%M:%S")
    uploaded_file = st.file_uploader("Choose a file (CSV, XLS, XLSX)", type=["csv", "xls", "xlsx"])

    if uploaded_file is not None:
        st.session_state.selected_dataset_name = uploaded_file.name
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

        # recherche du fichier de description
        uploaded_file_basename = os.path.basename(uploaded_file.name)
        desc_file = find_matching_description_file("./datasources", uploaded_file_basename)
        if desc_file:
            st.session_state.description_file_name = desc_file
            with open(desc_file, 'r') as f:
                field_descriptors = json.load(f)

            connector = PandasConnector(
                config={"original_df": data},
                field_descriptions=field_descriptors
            )
            sdf = SmartDataframe(connector, config=sdf_cfg)
        else:
            sdf = SmartDataframe(data, config=sdf_cfg)

        st.session_state.sdf = sdf
        nb_ln, nb_c = data.shape
        st.session_state.nb_ln = nb_ln
        st.session_state.nb_c = nb_c
        st.session_state.column_names = list(data.columns)

# affichage des infos sur le datasae
if st.session_state.sdf is not None:
    st.markdown(f"""<hr />
    <div class="analysis">
    Analysis for dataset : {st.session_state.selected_dataset_name}  on {st.session_state.study_date}
    </div>
    <br />   
    <h5>Dataset Shape :  </h5>lines : {st.session_state.nb_ln}, columns : {st.session_state.nb_c}
    <hr />
    <h5>Field names :  </h5>lines : " {', '.join(st.session_state.column_names)}"
    <hr />
    """, unsafe_allow_html=True)

    if st.session_state.description_file_name is not None:
        st.markdown(f"<h5>Fields Description file was found at : </h5> {st.session_state.description_file_name} <hr />",
                    unsafe_allow_html=True)
        # Saisie du prompt
    st.markdown("""
               <h4 style='text-align: left; color: #4F9493;'>
               <br>Now for this dataset, Enter your question in natural language  :<br> 
               </h4>
           """, unsafe_allow_html=True)
    st.text_area("Enter your prompt here and send it", value=st.session_state.input_text,
                 key="input_text")
    # Utilisation de st.empty() pour créer un espace réservé pour la réponse
    response_placeholder = st.empty()


    if not st.session_state.show_envoyer_button:
        answer = str(st.session_state.output_text)
        # print(answer)
        if answer.endswith(".png"):
            answer = f"Tour chart was created at\n{st.session_state.output_text}"
        response_placeholder.text_area("Response", value=answer, key="output_text_area", disabled=True)

    # affichage des boutons das une ligne
    col1, col2 = st.columns([2, 1])

    with col1:
        # Bouton envoyer
        if st.session_state.show_envoyer_button:
            st.button("Send", key="envoyer", help="Send the query to the server", on_click=handle_question, args=(st.session_state.sdf,))

    with col2:
        # Bouton Nouvelle question (visible seulement après la réponse)
        if st.session_state.show_new_question_button:
            st.button("New query", key="new_query", help="Last query and answer will be registrate. Ask an other question",
                      use_container_width=True, on_click=clear_input)


