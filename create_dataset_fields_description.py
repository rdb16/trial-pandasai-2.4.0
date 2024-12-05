import os.path

import pandas as pd
import json


# Charger le fichier CSV ou Excel
def load_file(_file_path):
    if _file_path.endswith('.csv'):
        df1 = pd.read_csv(_file_path)
    elif _file_path.endswith(('.xls', '.xlsx')):
        df1 = pd.read_excel(_file_path)
    else:
        raise ValueError("Le fichier doit être au format CSV ou Excel (xls, xlsx).")
    return df1


# Demander à l'utilisateur de définir le contenu de chaque colonne
def describe_columns(df):
    field_descriptions = {}
    for column in df.columns:
        description = input(f"Veuillez décrire le contenu de la colonne '{column}': ")
        field_descriptions[column] = description
    return field_descriptions


if __name__ == "__main__":
    # Demander le chemin du fichier à l'utilisateur
    file_path = input("Veuillez entrer le chemin du fichier CSV ou Excel: ")

    try:
        # Charger les données
        df = load_file(file_path)

        # Afficher un aperçu des données
        print("Aperçu des données:")
        print(df.head(3))

        # Demander les descriptions des colonnes
        descriptions = describe_columns(df)

        # Afficher les descriptions fournies par l'utilisateur
        print("Descriptions des colonnes:")
        for column, description in descriptions.items():
            print(f"{column}: {description}")

        # Sauvegarder les descriptions dans un fichier JSON
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        json_file_name = f"{base_name}_field_descriptions.json"
        svgd_path = os.path.join("./datasources", json_file_name)
        with open(svgd_path, 'w', encoding='utf-8') as json_file:
            json.dump(descriptions, json_file, indent=4, ensure_ascii=False)
        print(f"Descriptions des colonnes sauvegardées dans le fichier: {json_file_name}")

    except ValueError as e:
        print(e)
    except FileNotFoundError:
        print("Le fichier n'a pas été trouvé. Veuillez vérifier le chemin fourni.")
