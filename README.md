remplir un fichier .env avec :
## les données de connexion à une éventuelle base de données :
type="sql"
dialect="mysql"
username="xxx"
password="xxx"
host="example.com" # IP or URL
port=3306 # Port number
database="mydb" # Database name
## les données général_config.json
ne contiennent pa sde secret; elle configure des répertoires pour le projet , le rendu du pdf,
et des paramètres généraux, éventuels, en cas d'utilisation d'un LLM de Bedrock.
par défaut on utilisera Bamboo. dans cette hypothèse il faut rédiger les fichiers de descriptions
des champs en anglais, seule langue comprise par Bampboo.
## ce code utilise la version restreinte de pandas faite par PandasAI.
