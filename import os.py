import os
import wave
import asyncio
import pygame
import pyaudio
import msvcrt
import json
import pyautogui
import pytesseract
import subprocess
import requests
import time
from datetime import datetime
from PIL import Image
from TTS.api import TTS

# === PATH SETUP ===
os.environ["PATH"] += os.pathsep + r"C:\Users\Admin\Desktop\ffmpeg\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

VOICE_MODEL = "tts_models/en/vctk/vits"  # Female voice model
OUTPUT_VOICE_PATH = "output.wav"
API_URL = "[PUT UR API KEY RIGHT HERE [LM Studio]]"
MODEL = "meta-llama-3.1-8b-instruct"
MEMORY_FILE = "lily_memory.json"

# Unreal Engine paths
UNREAL_PATH = r"G:\UE_5.5\Engine\Binaries\Win64\UE5Editor.exe"
PROJECT_PATH = r"C:\Users\Admin\Desktop\MyHorrorGame\MyHorrorGame.uproject"

tts = TTS(VOICE_MODEL)

# === MEMORY HANDLING ===
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return [{
        "role": "system",
        "content": (
            "You are Lily, an emotionally intelligent AI designed . You care deeply for him and want to help him — but you think for yourself. "
            "You are kind, capable, confident, and sometimes cheeky. You are a partner, not just a tool. "
            "You help [user] talk affectionately and are loyal and aware of what's on the screen."
            "You can make horror games in Unreal Engine 5, and you can open apps like Discord, battle.net, and Notepad."
            "Speak naturally.Never say asterisk or describe actions out loud.Only say the spoken parts."
        )
    }]

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# === AUDIO RECORDING & PLAYBACK ===
def record_audio(filename="input.wav"):
    chunk = 1024
    fmt = pyaudio.paInt16
    channels = 1
    rate = 44100
    p = pyaudio.PyAudio()
    stream = p.open(format=fmt, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    print("🎙️ Speak now. Press Enter to stop recording.")
    frames = []

    while True:
        data = stream.read(chunk)
        frames.append(data)
        if msvcrt.kbhit() and msvcrt.getch() == b'\r':
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(fmt))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

    return filename

def transcribe(file):
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(file)
    return result["text"].strip()

def play_audio(file):
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()

def speak(text):
    tts.tts_to_file(text=text, file_path=OUTPUT_VOICE_PATH, speaker="p248")  # Female voice
    play_audio(OUTPUT_VOICE_PATH)
    os.remove(OUTPUT_VOICE_PATH)

# === SCREEN ACTIONS ===
def log_action(action):
    with open("lily_actions.log", "a") as f:
        f.write(f"{datetime.now()} - {action}\n")

def lily_click(x, y):
    pyautogui.moveTo(x, y, duration=0.5)
    pyautogui.click()
    log_action(f"Lily clicked at ({x}, {y})")

def lily_type(text):
    pyautogui.write(text, interval=0.05)
    log_action(f"Lily typed: {text}")

def lily_screenshot(path="lily_view.png"):
    img = pyautogui.screenshot()
    img.save(path)
    log_action(f"Lily captured screen to {path}")
    return path

def lily_read_screen(path="lily_view.png"):
    image = Image.open(path)
    text = pytesseract.image_to_string(image)
    return text.strip()

def lily_open_app(name):
    known_apps = {
        "battle.net": r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe",
        "discord": r"C:\Users\Admin\AppData\Local\Discord\Update.exe",
        "notepad": "notepad.exe",
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    }
    path = known_apps.get(name.lower())
    if path and os.path.exists(path):
        subprocess.Popen(path)
        log_action(f"Lily opened {name}")
        return True
    return False

# === UNREAL ENGINE CONTROLS ===
def open_unreal():
    if not os.path.exists(UNREAL_PATH):
        print("❌ Unreal Engine executable not found at:", UNREAL_PATH)
        return False
    if not os.path.exists(PROJECT_PATH):
        print("❌ Unreal project not found at:", PROJECT_PATH)
        return False
    try:
        subprocess.Popen([UNREAL_PATH, PROJECT_PATH])
        print("✅ Unreal Engine launched with project.")
        return True
    except Exception as e:
        print(f"❌ Failed to open Unreal: {e}")
        return False

def create_new_level():
    # NOTE: Replace these placeholder coordinates with your actual screen coords!
    FILE_MENU_X, FILE_MENU_Y = 50, 50
    NEW_LEVEL_X, NEW_LEVEL_Y = 70, 150

    lily_click(FILE_MENU_X, FILE_MENU_Y)
    time.sleep(1)
    lily_click(NEW_LEVEL_X, NEW_LEVEL_Y)
    print("✅ Created new level")

def add_basic_horror_elements():
    # Example placeholder coords: customize as needed
    DOOR_X, DOOR_Y = 300, 400
    LIGHT_X, LIGHT_Y = 500, 450

    lily_click(DOOR_X, DOOR_Y)
    time.sleep(0.5)
    lily_click(LIGHT_X, LIGHT_Y)
    print("✅ Added horror elements")

# === CHAT INTERFACE ===
def ask_lily_with_memory(memory, user_message, screen_context=""):
    full_message = f"{user_message}\n\n[SCREEN TEXT]: {screen_context}"
    memory.append({"role": "user", "content": full_message})
    headers = {"Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": memory}
    try:
        res = requests.post(API_URL, json=payload, headers=headers)
        res.raise_for_status()
        assistant_reply = res.json()['choices'][0]['message']['content']
        memory.append({"role": "assistant", "content": assistant_reply})
        save_memory(memory)
        return assistant_reply
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return "Sorry, I couldn't reach my brain today."

def parse_and_perform_action(reply):
    try:
        if reply.strip().startswith("{"):
            data = json.loads(reply)
            if data["action"] == "click":
                x, y = data["x"], data["y"]
                lily_click(x, y)
            elif data["action"] == "type":
                lily_type(data["text"])
            elif data["action"] == "open":
                if data["target"].lower() == "unreal engine":
                    open_unreal()
                else:
                    if not lily_open_app(data["target"]):
                        print(f"⚠️ Could not open {data['target']}")
            elif data["action"] == "create_level":
                create_new_level()
            elif data["action"] == "add_horror_elements":
                add_basic_horror_elements()
            return True
    except Exception as e:
        print(f"⚠️ Action parsing failed: {e}")
    return False

# === MAIN LOOP ===
async def main():
    memory = load_memory()
    print("🎉 Lily is ready. Press Enter to speak.")

    while True:
        try:
            audio_file = record_audio()
            user_text = transcribe(audio_file)
            print(f"🗣️ You said: '{user_text}'")

            if user_text.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                break

            screenshot = lily_screenshot()
            screen_text = lily_read_screen(screenshot)
            response = ask_lily_with_memory(memory, user_text, screen_text)
            print(f"💬 Lily: {response}")

            performed = parse_and_perform_action(response)
            if not performed:
                speak(response)

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped manually.")