import subprocess
import pyautogui
import time
from multiprocessing import Process, Queue
from multi_ai_runner import ai_worker

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
            # Lancer les IA avec une Queue pour récupérer les scores
            result_queue = Queue()
            processes = []
            for name in TEAM_NAMES:
                p = Process(target=ai_worker, args=(name, episode, result_queue))
                p.start()
                processes.append(p)

            # 🧠 On attend un peu que les IA se connectent puis on presse "Enter"
            wait_for_bots_and_press_enter()

            # Attendre la fin des IA (le serveur s’arrête à la fin du jeu)
            for p in processes:
                p.join()

            pyautogui.press("enter")

            # Récupérer les scores et chemins de modèles
            results = [result_queue.get() for _ in TEAM_NAMES]
            best = max(results, key=lambda x: x[1])  # x[1] = total_reward

            print(f"🏆 Meilleur modèle : {best[0]} avec score {best[1]}")
            # Sauvegarder le meilleur modèle sous un nom générique
            import shutil
            if best[2]:
                shutil.copy(best[2], f"models/best_model_episode_{episode}.h5")

        except Exception as e:
            print(f"⚠️ Erreur détectée : {e}")

        finally:
            server_process.kill()
            print("🛑 Serveur terminé.")
