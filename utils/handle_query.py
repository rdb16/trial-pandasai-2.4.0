import streamlit as st
import os
from pathlib import Path
import time
import uuid


def handle_query(sdf1):
    prompt1 = st.session_state.input_text.strip()
    if prompt1:
        with st.spinner(text='Waiting for llm answer !!'):
            try:
                response = sdf1.chat(prompt1)
            except Exception as e:
                st.error(f"Error when calling LLM : {e}")
                response = "An Error occurred. Please retry"

        st.session_state.output_text = response
        if response.endswith(".png"):
            default_chart_path = Path("exports/charts/temp_chart.png")
            final_chart_rep = "./exports/png/"
            if os.path.exists(default_chart_path):
                unique_file_path = final_chart_rep + get_unique_filename()
                default_chart_path.rename(Path(unique_file_path))
                response = unique_file_path

        st.session_state.session_data.append({"question": prompt1, "answer": response})
        st.session_state.show_envoyer_button = False
        st.session_state.show_new_question_button = True


# Generate a unique file name using a timestamp or UUID
def get_unique_filename(prefix="chart", extension=".png"):

    timestamp1 = time.strftime("%Y%m%d-%H%M%S")  # Timestamp for uniqueness
    unique_id = uuid.uuid4().hex[:8]  # Short UUID for uniqueness
    return f"{prefix}_{timestamp1}_{unique_id}{extension}"
