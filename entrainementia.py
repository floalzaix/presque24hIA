import subprocess
import pyautogui
import time
from multiprocessing import Process, Queue
from multi_ai_runner import ai_worker
import os

# 👉 Change ce chemin avec celui vers ton .exe
SERVER_EXECUTABLE_PATH = r"C:\Users\hgpereir\Documents\IA\iut\Serveur\HuntToSurvive_IHM.exe"

# 👉 Coordonnées du bouton "Lancer"
LAUNCH_BUTTON_POSITION = (1180, 568)  # À adapter si besoin

def launch_server_with_click():
    print("🟢 Lancement du serveur...")
    process = subprocess.Popen([SERVER_EXECUTABLE_PATH])
    time.sleep(2.5)  # Attendre que la fenêtre apparaisse
    print("🖱️  Clic sur le bouton 'Lancer'")
    pyautogui.click(*LAUNCH_BUTTON_POSITION)    
    return process

def wait_for_bots_and_press_enter(wait_time=5):
    print(f"⏳ Attente de {wait_time}s pour que les IA se connectent...")
    time.sleep(wait_time)
    print("⏎ Appui sur Entrée pour démarrer la partie")
    pyautogui.press("enter")

if __name__ == "__main__":
    NUM_EPISODES = 1000
    TEAM_NAMES = ["Alzaix", "Bot1", "Bot2", "Bot3"]

    for episode in range(NUM_EPISODES):
        print(f"\n🔁 Épisode {episode + 1} :")
        server_process = launch_server_with_click()

        try:
            # Chercher le modèle du meilleur épisode précédent
            if episode > 0:
                best_model_path = f"models/best_model_episode_{episode-1}.h5"
                if not os.path.exists(best_model_path):
                    best_model_path = None
            else:
                best_model_path = None

            result_queue = Queue()
            processes = []
            for name in TEAM_NAMES:
                # Passe best_model_path à chaque IA
                p = Process(target=ai_worker, args=(name, episode, result_queue, best_model_path))
                p.start()
                processes.append(p)

            wait_for_bots_and_press_enter()

            for p in processes:
                p.join()

            pyautogui.press("enter")

            results = [result_queue.get() for _ in TEAM_NAMES]
            best = max(results, key=lambda x: x[1])

            print(f"🏆 Meilleur modèle : {best[0]} avec score {best[1]}")
            import shutil
            if best[2]:
                os.makedirs("models", exist_ok=True)
                shutil.copy(best[2], f"models/best_model_episode_{episode}.h5")

        except Exception as e:
            print(f"⚠️ Erreur détectée : {e}")

        finally:
            server_process.kill()
            print("🛑 Serveur terminé.")
