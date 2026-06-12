
Smart File Organizer
This script automatically sorts documents, code, AI models, audio, video, and more into specific folders, applying rules and protections to avoid moving critical files.

---

## 🚀 Main Features
- 📂 Automatic sorting by extension and size.
- 🔒 Protection of critical folders and files.
- 📦 Detection of complete projects (repositories with `package.json`, `.git`, etc.).
- ♻️ Duplicate detection using MD5 hash.
- 🧪 Simulation mode to test without moving anything.
- 📝 Detailed logs of each run.

- Simulation mode (recommended first):

bash
python carpetas.py --simulate
→ Shows what the script would do without moving any files.

Real mode:

bash
python carpetas.py
→ Moves and organizes the files according to the rules.

---

## 🔧 Code Configuration
The script is designed to be adaptable. Before running it, review these variables in `carpetas.py`:

- **`CARPETA_RAIZ`**
- 
  📍 Main path where files will be organized.  
  **What to do:** change it to the folder you want to organize on your PC.  
  ```python
  CARPETA_RAIZ = Path(r"C:\Users\YourUser\Documents")
CARPETAS_BLINDADAS  
🛡 List of folders that will never be moved or touched.
What to do: add here the critical folders in your environment (e.g., node_modules, .git).

UMBRAL_MODELO_PESADO_MB  
⚖️ Defines the size (in MB) from which a file is considered a “heavy AI model” and moved to Modelos_IA.
What to do: adjust according to your hardware.

REGLAS_POR_EXTENSION  
📂 Dictionary that assigns folders based on file extension.
What to do: edit it if you want certain file types to go to another folder.
Example: move .csv to datasets instead of Bases_de_Datos.

ARCHIVOS_INTOCABLES_RAIZ  
🔒 Files in the root that will never be moved (e.g., README.md, requirements.txt).
What to do: add here any file you want to keep fixed.

📂 Example Organization
documents/ → PDF, DOCX, TXT

scripts/ → Source code (Python, JS, etc.)

audio/ → Audio files

video/ → Video files

AI_Models/ → AI weights and models

GitHub_Repositories/ → Complete detected projects

📝 Customization Example
If you work with Arduino projects, you can add this rule:

python
REGLAS_POR_EXTENSION[".ino"] = "scripts"
This way all your Arduino sketches will go into the scripts folder.

⚠️ Warnings
Always test first in simulation mode.

Do not run in system folders or with sensitive files.

The script renames files to avoid collisions (config_v1.json, etc.).

📜 License
This project is under the MIT license.
You can use, modify, and distribute it freely, always giving credit to the original author.

🌟 Contributions
Contributions are welcome!
If you have ideas to improve the organizer, open an issue or send a pull request.

👨‍💻 Author
Developed by Gabriel Vallejo Castro  
aka thegaballs or s.gaballs  

## ⚙️ Installation
1. Clone the repository:
```bash
  git clone https://github.com/gaballs05/smart-organizer.git
   cd smart-organizer
