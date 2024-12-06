import os
import re


def find_matching_description_file(rep, target):
    # Extraire le nom sans extension du fichier cible
    base_name = os.path.splitext(target)[0]
    # Définir le motif recherché : commence par le nom sans extension, se termine par 'descriptions.json'
    pattern = re.compile(f"^{re.escape(base_name)}.*descriptions\.json$")

    # Parcourir les fichiers dans le répertoire donné
    for file_name in os.listdir(rep):
        # Vérifier si le fichier correspond au motif
        if pattern.match(file_name):
            return os.path.join(rep, file_name)

    # Si aucun fichier correspondant n'est trouvé, retourner None
    return None


# Exemple d'utilisation
if __name__ == "__main__":
    directory = "../datasources"
    target_filename = "pinguin.csv"
    matching_file = find_matching_description_file(directory, target_filename)

    if matching_file:
        print(f"Fichier correspondant trouvé : {matching_file}")
    else:
        print("Aucun fichier correspondant trouvé.")
