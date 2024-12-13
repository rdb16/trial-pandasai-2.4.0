"""
Example of using displaying PandasAI charts in Streamlit

Usage:
streamlit run examples/using_streamlit.py
"""
import os
import time
import uuid
from pathlib import Path
from filelock import FileLock, Timeout
import pandas as pd
import streamlit as st

from api_keys import PANDASAI_API_KEY
from pandasai import Agent
from pandasai.responses.streamlit_response import StreamlitResponse


# Generate a unique file name using a timestamp or UUID
def get_unique_filename(base_dir, prefix="chart", extension=".png"):
    timestamp = time.strftime("%Y%m%d-%H%M%S")  # Timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:8]  # Short UUID for uniqueness
    return base_dir / f"{prefix}_{timestamp}_{unique_id}{extension}"


employees_df = pd.DataFrame(
    {
        "EmployeeID": [1, 2, 3, 4, 5],
        "Name": ["John", "Emma", "Liam", "Olivia", "William"],
        "Department": ["HR", "Sales", "IT", "Marketing", "Finance"],
    }
)

salaries_df = pd.DataFrame(
    {
        "EmployeeID": [1, 2, 3, 4, 5],
        "Salary": [5000, 6000, 4500, 7000, 5500],
    }
)

svg_dir = Path("exports/charts")
svg_dir.mkdir(parents=True, exist_ok=True)

# vérification de la génération du graphe
default_chart_path = svg_dir / "temp_chart.png"
lock_path = default_chart_path.with_suffix(".lock")  # le verrou
lock = FileLock(lock_path)

os.environ["PANDASAI_API_KEY"] = PANDASAI_API_KEY

agent = Agent(
    [employees_df, salaries_df],
    config={"verbose": True, "response_parser": StreamlitResponse},
)

# Tester si un verrou existe avant d'exécuter agent.chat()
try:
    lock.acquire(timeout=5) # Essayer d'acquérir le verrou
    response = agent.chat("Plot salaries against employee name")

    if default_chart_path.exists():
        unique_chart_path = get_unique_filename(svg_dir)
        default_chart_path.rename(unique_chart_path)
        st.write(f"Chart saved to {unique_chart_path}")
        # streamlit.image(str(unique_chart_path))
    else:
        st.write("No Chart generated")
        st.write(response)
finally:
    if lock.is_locked:  # Vérifier si le verrou est encore actif
        lock.release()  # Libérer le verrou
        # Supprimer explicitement le fichier .lock
    if lock_path.exists():
        lock_path.unlink()  # Supprime le fichier .lock
