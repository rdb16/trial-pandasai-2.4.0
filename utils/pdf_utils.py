import datetime
import os
from PIL import Image
from fpdf import FPDF
import pandas as pd


class CustomPDF(FPDF):
    def footer(self):
        # à 15mm du bas
        self.set_y(-15)

        # Libellé centré
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(128)
        # réduire l'interligne à 5 (h)
        self.cell(0, 5, "Powered by SNTP Capitalisation", ln=True, align="C")

        # Copyrights centré
        self.set_y(-12)
        self.set_font("DejaVu", size=8)
        self.cell(0, 5, "© 2024-2025 All rights reserved.", align="C")
        self.set_text_color(0, 0, 0)

        # numéro de page
        self.set_y(-9)
        self.set_font("DejaVu", size=8)
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, align="C")

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
                self.multi_cell(col_width, line_height, txt=str(value), border=1, align='L')
                x_start += col_width
                # Revenir à la position de la cellule suivante sur la ligne
                self.set_xy(x_start, y_start)
            self.ln(max_line_height)


# génère un pdf
def create_kai_pdf(csv_file_name, df, data):
    csv_basename = os.path.basename(csv_file_name)
    pdf = CustomPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    # Ajouter une police Unicode
    pdf.add_font("DejaVu", "", "./fonts/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "./fonts/dejavu-sans.bold.ttf", uni=True)
    pdf.add_font("DejaVu", "I", "./fonts/dejavu-sans.oblique.ttf", uni=True)

    pdf.set_font("DejaVu", size=12)
    pdf.add_page()
    logo_path = "./logo/sntpk-ia-logo.jpeg"
    pdf.image(logo_path, x=(210 - 30) / 2, y=10, w=30)  # centré pour largeur logo 30

    # Ajouter la date du jour
    pdf.set_y(31)  # Position sous le logo
    pdf.set_x(150)  # position horizontale
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, txt=f"Date : {datetime.datetime.now().strftime('%d/%m/%Y')}", ln=True, align="R")

    # Ajouter le nom du fichier CSV dans un encadré
    pdf.ln(5)  # Espacement
    pdf.set_font("DejaVu", style="B", size=12)
    pdf.set_fill_color(0, 0, 128)  # Bleu marine
    pdf.set_text_color(255, 255, 255)  # Blanc
    pdf.cell(0, 10, txt=f"Rapport d'analyse du dataset {csv_file_name}", border=1, ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)  # Retour à la couleur noire par défaut

    # centré le titre
    pdf.ln(5)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, txt="Session Questions/Réponses", ln=True, align="C")
    pdf.ln(10)  # Espacement

    for entry in data:
        pdf.set_font("DejaVu", "B", size=12)
        # Insérer une ligne bleue après chaque entrée
        pdf.set_line_width(0.7)
        pdf.set_draw_color(0, 0, 255)
        pdf.line((210 - 30) / 2, pdf.get_y() + 5, (210 + 30) / 2, pdf.get_y() + 5)
        pdf.ln(10)

        pdf.set_draw_color(0, 0, 0)

        if entry['question'] == "Aperçu du Dataset":
            # Ajouter un tableau des premières lignes du DataFrame
            pdf.set_font("DejaVu", "B", size=14)
            pdf.cell(0, 10, txt="Aperçu des premières lignes du Dataset:", ln=True, align="L")
            pdf.ln(5)

            # Créer le tableau à partir des premières lignes du dataframe
            pdf.create_table(df.head(3))
            pdf.ln(20)
            continue

        pdf.set_font("DejaVu", 'B', size=12)
        pdf.multi_cell(0, 10, txt=f"Question: {entry['question']}", align="L")
        pdf.set_font("DejaVu", size=12)
        if isinstance(entry['answer'], str) and entry['answer'].endswith(".png"):
            image_path = entry['answer']
            pdf.multi_cell(0, 10, txt="Réponse: Voir le graphique ci-dessous.")
            image_height = 70 * (Image.open(image_path).height / Image.open(image_path).width)
            available_height = 297 - pdf.get_y() - 15
            # print("available: ", available_height, "logo-height : ", image_height, "y : ", pdf.get_y())

            # Si l'espace disponible est insuffisant, passer à une nouvelle page
            if available_height < image_height + 5:
                pdf.ln(available_height + 20)
                pdf.add_page()

            pdf.image(entry["answer"], x=10, y=pdf.get_y(), w=70)  # Ajuster la largeur pour s'adapter à la page
            # Calculer la hauteur de l'image et décaler en conséquence
            pdf.ln(image_height + 5)
        else:
            pdf.multi_cell(0, 10, txt=f"Réponse: {entry['answer']}")
            pdf.ln(5)

        pdf.ln(5)

    # Créer le répertoire Results s'il n'existe pas
    if not os.path.exists("Results"):
        os.makedirs("Results")

    # Nommer le pdf
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    pdf_file_name = f"analysis-{csv_basename}-{timestamp}.pdf"
    # debug
    # print(pdf_file)

    pdf_path = os.path.join("Results", pdf_file_name)
    pdf.output(pdf_path)
    return pdf_path


if __name__ == "__main__":
    csv = "datasets/titanic.csv"
    df = pd.read_csv(csv)
    data_session = [
        {"question": "What is the capital1?", "answer": "exports/charts/8de7254f-c7ac-4b39-a643-9cbd7824c245.png"},
        {"question": "What is the capital2?", "answer": "exports/charts/c14665f4-f411-41a8-8ab2-d8010277e04f.png"},
        {"question": "What is the capital3?", "answer": "exports/charts/c14665f4-f411-41a8-8ab2-d8010277e04f.png"},
        {"question": "What is the capital4?", "answer": "exports/charts/c14665f4-f411-41a8-8ab2-d8010277e04f.png"}
    ]
    path = create_kai_pdf(csv, df, data_session)
    print(path)
