import json

import streamlit as st
import pandas as pd
from PIL import Image
import boto3
from pandasai import SmartDataframe
from pandasai.llm import BedrockClaude
from pandasai.schemas.df_config import Config
from utils.pdf_utils import create_kai_pdf
from utils.get_aws_llm import get_aws_llm

# Configuration de la page
st.set_page_config(page_title="SNTP Capitalisation", page_icon="\U0001F4B0", layout="centered")


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

st.markdown(f"<style>{get_css_style()}</style>", unsafe_allow_html=True)
st.image(get_logo(), width=100, caption=None)
