import datetime
import json
import os
import time
import uuid
from pathlib import Path
import streamlit as st
import pandasai.pandas as pd
from PIL import Image
# import boto3
from filelock import FileLock
from pandasai import SmartDataframe
from pandasai.schemas.df_config import Config
from pandasai.connectors import PandasConnector
from utils.pdf_utils import create_k_report_pdf
# from utils.aws_llm import get_aws_llm

from utils.bamboo_llm import get_bamboo_llm
from utils.match_descriptions_file import find_matching_description_file


# Fonction pour nettoyer le champ d'input
def clear_input():
    st.session_state.input_text = ""
    st.session_state.output_text = ""
    st.session_state.show_new_question_button = False
    st.session_state.show_send_button = True


def handle_query(sdf1, prompt1):
    if prompt1:
        with st.spinner(text='Waiting for llm answer !!'):
            try:
                response = sdf1.chat(prompt1)
            except Exception as e:
                st.error(f"Error when calling LLM : {e}")
                response = "An Error occurred. Please retry"

        if isinstance(response, str) and response.endswith(".png"):
            default_chart_path = Path("exports/charts/temp_chart.png")
            final_chart_rep = "./exports/png/"
            if os.path.exists(default_chart_path):
                unique_file_path = final_chart_rep + get_unique_filename()
                default_chart_path.rename(Path(unique_file_path))
                response = unique_file_path

        st.session_state.output_text = str(response)
        st.session_state.session_data.append({"question": prompt1, "answer": str(response)})
        st.session_state.show_send_button = False
        st.session_state.show_new_question_button = True


# Generate a unique file name using a timestamp or UUID
def get_unique_filename(prefix="chart", extension=".png"):
    timestamp1 = time.strftime("%Y%m%d-%H%M%S")  # Timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:8]  # Short UUID for uniqueness
    return f"{prefix}_{timestamp1}_{unique_id}{extension}"


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

if 'show_send_button' not in st.session_state:
    st.session_state.show_send_button = True

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

if 'output_text' not in st.session_state:
    st.session_state.output_text = ""

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
    with open('general_config.json', 'r') as f_conf:
        return json.load(f_conf)


@st.cache_resource
def get_css_style():
    with open("assets/styles/style.css", "r") as f_css:
        return f_css.read()


@st.cache_resource
def get_logo():
    logo = Image.open("assets/logo/sntpk-ia-logo.jpeg")
    return logo


config = read_conf()
# llm = get_aws_llm(config)
llm = get_bamboo_llm()
if llm is None:
    st.warning("No AWS LLM detected")

st.markdown(f"<style>{get_css_style()}</style>", unsafe_allow_html=True)
st.image(get_logo(), width=100, caption=None)
st.markdown("""
    <div class="title">
        Usage Report <br>Streamlit for PandasAI <br> on AWS Bedrock Claude 3.0 <br>  or Bamboo_LLM
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

        st.session_state.data = data

        sdf_cfg = Config(
            llm=llm,
            model=config['aws_model'],
            max_tokens=config['llm_max_tokens'],
            temperature=config['llm_temperature'],
            save_charts_path=config['chart_export_path']
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

# affichage des infos sur le datasae
if 'sdf' in st.session_state and st.session_state.sdf is not None:
    nb_ln, nb_c = st.session_state.data.shape
    col_list = list(st.session_state.data.columns)
    st.markdown(f"""<hr />
    <div class="analysis">
    Analysis for dataset : {st.session_state.selected_dataset_name}  on {st.session_state.study_date}
    </div>
    <br />   
    <h5>Dataset Shape :  </h5>lines : {nb_ln}, columns : {nb_c}
    <hr />
    <h5>Field names :  </h5>:  {col_list}
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
    st.text_area("Enter your prompt here and send it", value=st.session_state.input_text, key="input_text")
    # Utilisation de st.empty() pour créer un espace réservé pour la réponse
    response_placeholder = st.empty()

    if st.session_state and not st.session_state.show_send_button:
        answer = st.session_state.output_text
        response_placeholder.text_area("Response : ", value=str(answer) if answer is not None else "", key="output_text", disabled=True)

    # affichage des boutons das une ligne
    col1, col2 = st.columns([2, 1])

    with col1:
        # Bouton send
        if st.session_state.show_send_button:
            prompt  = st.session_state.input_text.strip() if st.session_state.input_text is not None else ""
            st.button("Send", key="send", help="Send the query to the server", on_click=handle_query, args=(st.session_state.sdf, prompt,))

    with col2:
        # Bouton Nouvelle question (visible seulement après la réponse)
        if st.session_state.show_new_question_button:
            st.button("New query", key="new_query", help="Last query and answer will be registrate. Ask an other question", use_container_width=True, on_click=clear_input)

    # Bouton Archiver pour générer un PDF
    if st.button("Stop & Archive", key="archive", help="save to PDF", use_container_width=True, kwargs={"kind": "primary"}):
        # debug
        with open('debug.txt', 'a') as f:
            for item in st.session_state.session_data:
                f.write(f'\n{item}')

        csv_name = os.path.basename(st.session_state.selected_dataset_name)
        pdf_path = create_k_report_pdf(config, csv_name, st.session_state.session_data, st.session_state.data)

        st.success(f"PDF généré avec succès : {pdf_path}")
        st.write(f"[Télécharger le PDF]({pdf_path})")
