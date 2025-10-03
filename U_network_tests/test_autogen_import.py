# test_autogen_import.py

try:
    from autogen import ConversableAgent

    print("✅ Import réussi : la classe ConversableAgent est accessible.")
    print(f"Classe ConversableAgent : {ConversableAgent}")
except ImportError as e:
    print("❌ Erreur d'import :", e)
    print("Vérifiez que vous avez bien installé le package pyautogen dans le bon environnement Python.")
except Exception as e:
    print("❌ Autre erreur :", e)

# Vérification du chemin de l'interpréteur Python
import sys
print("\nInterpréteur Python utilisé :", sys.executable)

# Vérification des modules installés
try:
    import pkg_resources
    autogen_installed = any(pkg.key == "pyautogen" for pkg in pkg_resources.working_set)
    print("pyautogen est installé :", autogen_installed)
except:
    print("⚠️ Impossible de vérifier les paquets installés.")
