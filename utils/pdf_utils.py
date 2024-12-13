import datetime
import os
import json
from PIL import Image
from fpdf import FPDF, FPDFException
from fpdf.enums import XPos, YPos
from textwrap import wrap
import pandas as pd


class CustomPDF(FPDF):
    def footer(self):
        # à 15mm du bas
        self.set_y(-15)

        # Libellé centré
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(128)
        # réduire l'interligne à 5 (h)
        self.cell(0, 5, "Powered by SNTP Capitalisation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        # Copyrights centré
        self.set_y(-12)
        self.set_font("DejaVu", size=8)
        self.cell(0, 5, "© 2024-2025 All rights reserved.", align="C")
        self.set_text_color(0, 0, 0)

        # numéro de page
        self.set_y(-9)
        self.set_font("DejaVu", size=8)
        self.cell(0, 5, f'Page {self.page_no()}', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align="C")

    def create_table(self, dataframe):
        # Définir la largeur des colonnes
        col_width = self.w / (len(dataframe.columns) + 1)
        row_height = 7
        line_height = 5

        # Ajouter l'entête du tableau
        self.set_font("DejaVu", "B", size=7)
        for column in dataframe.columns:
            self.cell(col_width, row_height, txt=str(column), border=1, align='C')
        self.ln(row_height)

        # Ajouter les lignes du tableau avec la gestion des hauteurs
        self.set_font("DejaVu", size=7)
        for _, row in dataframe.iterrows():
            # calcul de la hauteur max
            max_line_height = row_height
            cell_values = []
            for value in row:
                text = str(value)
                nb_lines = int(self.get_string_width(text) / col_width + 1)
                max_line_height = max(max_line_height, line_height * nb_lines)
                cell_values.append(text)

            # rempli chaque cellule de la ligne avec Max
            x_start = self.get_x()
            y_start = self.get_y()
            for value in row:
                # Utiliser multi_cell pour gérer les cellules qui contiennent un long texte
                try:
                    # Split the text into manageable chunks if too long for the cell width
                    wrapped_text = "\n".join(wrap(str(value), width=int(col_width / self.get_string_width('A'))))
                    self.multi_cell(col_width, line_height, txt=wrapped_text, border=1, align='L')
                except FPDFException as e:
                    self.set_font('DejaVu', size=10)  # Reduce font size as fallback
                    self.multi_cell(col_width, line_height, txt=str(value), border=1, align='L')

                x_start += col_width
                # Revenir à la position de la cellule suivante sur la ligne
                self.set_xy(x_start, y_start)
                self.ln(max_line_height)


# génère un pdf
def create_k_report_pdf(cfg, csv_file_name, q_a, df):
    # print(q_a)
    csv_basename = os.path.basename(csv_file_name)
    pdf = CustomPDF(
        orientation=cfg['pdf_page_orientation'],
        unit=cfg['pdf_unit'],
        format=cfg['pdf_page_format']
    )
    pdf.set_auto_page_break(auto=True, margin=15)
    # Ajouter une police Unicode
    pdf.add_font("DejaVu", "", "./assets/fonts/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "./assets/fonts/dejavu-sans.bold.ttf")
    pdf.add_font("DejaVu", "I", "./assets/fonts/dejavu-sans.oblique.ttf")

    pdf.set_font("DejaVu", size=12)
    pdf.add_page()
    logo_path = cfg['logo_path']
    pdf.image(logo_path, x=(210 - 30) / 2, y=10, w=30)  # centré pour largeur logo 30

    # Ajouter la date du jour
    pdf.set_y(31)  # Position sous le logo
    pdf.set_x(150)  # position horizontale
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, text=f"Date : {datetime.datetime.now().strftime('%d/%m/%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R")

    # Ajouter le nom du fichier CSV dans un encadré
    pdf.ln(5)  # Espacement
    pdf.set_font("DejaVu", style="B", size=12)
    pdf.set_fill_color(0, 0, 128)  # Bleu marine
    pdf.set_text_color(255, 255, 255)  # Blanc
    pdf.cell(0, 10, text=f"Dataset Reporting {csv_file_name}", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)  # Retour à la couleur noire par défaut

    # aperçu du dataset
    pdf.set_font("DejaVu", "B", size=14)
    pdf.cell(0, 10, text="Dataset overview:", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    pdf.ln(5)

    # centré le titre
    # pdf.ln(5)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, text="Session QUERY/RESPONSE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(10)  # Espacement
    nb_ln, nb_col = df.shape
    pdf.cell(0, 10, text=f"Number of lines: {nb_ln}, Number of columns: {nb_col}")
    pdf.ln(10)
    pdf.cell(0, 10, text="Field titles", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
    current_line = ""
    max_line_length = 76
    col_list = list(df.columns)
    for col in col_list:
        # Ajouter le titre de la colonne à la ligne actuelle
        if len(current_line) + len(col) + 2 <= max_line_length:  # "+2" pour la virgule et l'espace
            current_line += f"{col}, "
        else:
            # Imprimer la ligne actuelle et commencer une nouvelle
            pdf.cell(0, 10, text=current_line.strip(", "), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
            current_line = f"{col}, "

        # Imprimer la dernière ligne si elle n'est pas vide
    if current_line:
        pdf.cell(0, 10, text=current_line.strip(", "), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    pdf.ln(5)
    for entry in q_a:
        pdf.set_font("DejaVu", "B", size=12)
        # Insérer une ligne bleue après chaque entrée
        pdf.set_line_width(0.7)
        pdf.set_draw_color(0, 0, 255)
        pdf.line((210 - 30) / 2, pdf.get_y() + 5, (210 + 30) / 2, pdf.get_y() + 5)
        pdf.ln(5)
        pdf.set_draw_color(0, 0, 0)

        cell_width = pdf.w - pdf.l_margin - pdf.r_margin - 2

        pdf.set_font("DejaVu", 'B', size=12)
        pdf.set_x(pdf.l_margin + 2)
        pdf.cell(0, 10, align="L", text="Question :")
        pdf.ln(6)
        pdf.set_x(pdf.l_margin + 2)
        pdf.set_font("DejaVu", size=10)
        try:
            wrapped_question = "\n".join(wrap(entry['question'], width=80))
            pdf.multi_cell(cell_width, 10, text=wrapped_question, align="L")
        except FPDFException as e:
            pdf.set_font('DejaVu', size=10)  # Fallback to smaller font for long questions
            pdf.multi_cell(0, 10, text=f"Question: {entry['question']}", align="L")

        pdf.set_font("DejaVu", size=12)

        if isinstance(entry['answer'], str) and entry['answer'].endswith(".png"):
            image_path = entry['answer']
            pdf.set_x(pdf.l_margin + 2)
            pdf.multi_cell(cell_width, 10, text="Answer: See the chart below.")
            image_height = 70 * (Image.open(image_path).height / Image.open(image_path).width)
            available_height = 297 - pdf.get_y() - 15
            # print("available: ", available_height, "logo-height : ", image_height, "y : ", pdf.get_y())
            # Si l'espace disponible est insuffisant, passer à une nouvelle page
            if available_height < image_height + 5:
                # pdf.ln(available_height + 20)
                pdf.add_page()

            pdf.image(entry["answer"], x=10, y=pdf.get_y(), w=70)  # Ajuster la largeur pour s'adapter à la page
            # Calculer la hauteur de l'image et décaler en conséquence
            pdf.ln(image_height + 5)

        elif isinstance(entry['answer'], pd.DataFrame):
            pdf.set_font("DejaVu", 'B', size=12)
            pdf.set_x(pdf.l_margin + 2)
            pdf.cell(0, 10, align="L", text="Answer :")
            pdf.ln(6)
            df_string = entry['answer'].to_string(index=False)
            pdf.multi_cell(cell_width, 10, text=df_string, align="L")

        else:
            pdf.set_font("DejaVu", 'B', size=12)
            pdf.set_x(pdf.l_margin + 2)
            pdf.cell(0, 10, align="L", text="Answer :")
            pdf.ln(6)
            pdf.set_font("DejaVu", size=10)
            pdf.set_x(pdf.l_margin + 2)
            answer = entry["answer"]
            # print("answer", answer)
            wrapped_answer = "\n".join(wrap(answer, width=76))
            # print("wrapped_answer", wrapped_answer)
            available_width = pdf.w - pdf.l_margin - pdf.r_margin
            # print(f"Largeur disponible : {available_width}")
            # print("largeur calculée: ", pdf.get_string_width(wrapped_answer))
            pdf.set_x(pdf.l_margin + 2)
            try:
                pdf.multi_cell(cell_width, 10, text=wrapped_answer, align="L" )
            except FPDFException as e:
                pdf.set_font('DejaVu', size=10)  # Fallback to smaller font for long responses
                pdf.multi_cell(0, 10, txt=f"Response: {wrapped_answer}")
            pdf.ln(5)

    # Créer le répertoire Results s'il n'existe pas
    results = cfg['pdf_export_path']
    if not os.path.exists(results):
        os.makedirs(results)

    # Nommer le pdf
    timestamp = datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    pdf_file_name = f"analysis-{csv_basename}-{timestamp}.pdf"
    # debug
    # print(pdf_file)

    pdf_path = os.path.join(results, pdf_file_name)
    pdf.output(pdf_path)
    return pdf_path


if __name__ == "__main__":
    # pour les test lancer pdfutils dans le REP RACINE
    os.chdir('../')
    csv = "./datasources/titanic.csv"
    df = pd.read_csv(csv)
    with open("./general_config.json", 'r') as f:
        config = json.load(f)
    data_session = [
        {"question": "What is the capital1?", "answer": "BLA BLA BLA BLA BLA BLA BLA"},
        {"question": "What is the capital2?", "answer": "AZEERTTYUUIOP%MLKJHGGFDSQWXCVBN12365477 88AZEERTTYUUIOP%MLKJHGGF DSQWXCVBN1236547788- --AZEERTTYUUIOP%MLKJHGGFDSQWXCVBN1236547788---AZEERTTYUUIOP%MLKJHGGFDSQWXCVBN1236547788"},
        {"question": "Show the plot1", "answer": "./exports/png/chart_20241211-121536_398c94eb.png"},
        {"question": "Show the plot2", "answer": "exports/png/chart_20241210-195949_e99a9096.png"},
        {"question": "Plot the survival passengers, by embarked harbor and sex", "answer": "exports/png/chart_20241210-183836_87028061.png"}
    ]
    path = create_k_report_pdf(config, csv, data_session, df)
    print(path)
