"""
Jarvis Full — Single-file voice assistant with Tkinter GUI and many features.
Save as: jarvis_full.py
Run inside an active venv: python jarvis_full.py
"""

import os
import sys
import time
import threading
import datetime
import webbrowser
import random
import json
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# Audio / speech / recognition
import pyttsx3
import speech_recognition as sr

# Utilities / features
import wikipedia
import requests
import pywhatkit as kit
import pyautogui
import psutil
import pyjokes
from bs4 import BeautifulSoup
from pywikihow import search_wikihow
import PyPDF2
import cv2
import operator

# Third-party APIs
import vonage
import wolframalpha

# --------------------------- CONFIG (your API keys) ---------------------------
NEWS_API_KEY        = "28e0485191934748be9d185f1d48304d"
WEATHER_API_KEY     = "93f3f511a93bfc75850a23ed15f65e6f"
WOLFRAM_APP_ID      = "HKXJ9RXV6T"
VONAGE_API_KEY      = "ac722561"
VONAGE_API_SECRET   = "VkeNSTAZu7EvzWZa"
ALPHAVANTAGE_API_KEY= "65CWO82XYB6S1HFK"
# ------------------------------------------------------------------------------

# --------------------------- TTS & Recognizer init ----------------------------
# pyttsx3 init (SAPI5 on Windows)
try:
    engine = pyttsx3.init('sapi5' if os.name == 'nt' else None)
except Exception:
    engine = pyttsx3.init()
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)

recognizer = sr.Recognizer()
# ------------------------------------------------------------------------------

# --------------------------- helper utilities --------------------------------
def speak(text, chunk_size=900):
    """Speak text (chunked to avoid very long TTS issues)."""
    if not text:
        return
    # break long text into chunks at sentence boundaries
    sentences = []
    s = text.strip()
    while s:
        if len(s) <= chunk_size:
            sentences.append(s)
            break
        # try split at last period within chunk
        cut = s.rfind('.', 0, chunk_size)
        if cut == -1:
            cut = chunk_size
        sentences.append(s[:cut+1].strip())
        s = s[cut+1:].strip()
    for seg in sentences:
        engine.say(seg)
        engine.runAndWait()

def safe_request_get(url, timeout=8):
    try:
        return requests.get(url, timeout=timeout)
    except Exception as e:
        print("HTTP request failed:", e)
        return None
# ------------------------------------------------------------------------------

# --------------------------- voice input ------------------------------------
def listen_once(timeout=6, phrase_time_limit=6):
    """Listen once and return recognized string or None."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio, language='en-in')
        return text.lower()
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print("listen error:", e)
        return None
# ------------------------------------------------------------------------------

# --------------------------- features ---------------------------------------
# small helpers for filesystem
HOME = Path.home()
SCREENSHOT_DIR = HOME / "Pictures" / "Jarvis_Screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def wish_me():
    h = datetime.datetime.now().hour
    if h < 12:
        greet = "Good morning"
    elif h < 18:
        greet = "Good afternoon"
    else:
        greet = "Good evening"
    speak(f"{greet}. I am Jarvis. How can I help you today?")

def open_website(url):
    webbrowser.open(url)

def search_wikipedia(query):
    try:
        res = wikipedia.summary(query, sentences=2)
        speak(res)
        return res
    except Exception as e:
        speak("Could not fetch from Wikipedia.")
        return ""

def play_on_youtube(query):
    try:
        kit.playonyt(query)
        speak(f"Playing {query} on YouTube")
    except Exception as e:
        print("YouTube error:", e)
        speak("Unable to play YouTube right now.")

def get_news():
    if not NEWS_API_KEY or NEWS_API_KEY.startswith("YOUR_"):
        speak("News API key not configured.")
        return
    url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
    r = safe_request_get(url)
    if not r:
        speak("Unable to fetch news.")
        return
    data = r.json()
    articles = data.get("articles", [])[:5]
    if not articles:
        speak("No news found.")
        return
    for i, a in enumerate(articles, 1):
        title = a.get("title", "No title")
        speak(f"Headline {i}: {title}")
        time.sleep(0.2)

def get_weather(city):
    if not WEATHER_API_KEY or WEATHER_API_KEY.startswith("YOUR_"):
        speak("Weather API key not configured.")
        return None
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    r = safe_request_get(url)
    if not r:
        return None
    data = r.json()
    if data.get("cod") == "404":
        return None
    return {
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "desc": data["weather"][0]["description"],
        "wind": data["wind"]["speed"]
    }

def take_screenshot(save_path: Path=None):
    if save_path is None:
        save_path = SCREENSHOT_DIR / f"screenshot_{int(time.time())}.png"
    img = pyautogui.screenshot()
    img.save(str(save_path))
    speak(f"Screenshot saved to {save_path}")
    return str(save_path)

def capture_photo(save_path: Path=None):
    if save_path is None:
        save_path = SCREENSHOT_DIR / f"photo_{int(time.time())}.png"
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == 'nt' else 0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        speak("Camera not available.")
        return None
    cv2.imwrite(str(save_path), frame)
    speak(f"Photo saved to {save_path}")
    return str(save_path)

def read_pdf(path, page_no=0):
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if page_no < 0 or page_no >= len(reader.pages):
                speak("Invalid page number.")
                return ""
            text = reader.pages[page_no].extract_text() or ""
            # speak up to a reasonable length
            speak(text[:1500])
            return text
    except Exception as e:
        print("PDF read error:", e)
        speak("Failed to read PDF.")
        return ""

def translate_text(text, dest):
    try:
        from googletrans import Translator
        t = Translator()
        out = t.translate(text, dest=dest).text
        speak(out)
        return out
    except Exception as e:
        print("translate error:", e)
        speak("Translation failed.")
        return None

def send_sms_vonage(sender, to_number, text):
    if VONAGE_API_KEY.startswith("YOUR_"):
        speak("Vonage not configured.")
        return False
    try:
        client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_API_SECRET)
        sms = vonage.Sms(client)
        resp = sms.send_message({"from": sender, "to": to_number, "text": text})
        status = resp["messages"][0]["status"]
        if status == "0":
            speak("Message sent successfully.")
            return True
        else:
            speak("Message failed.")
            return False
    except Exception as e:
        print("vonage error:", e)
        speak("Failed to send message.")
        return False

def get_stock_price(symbol):
    if ALPHAVANTAGE_API_KEY.startswith("YOUR_"):
        speak("Alpha Vantage key not configured.")
        return None
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
    r = safe_request_get(url)
    if not r:
        return None
    data = r.json()
    try:
        price = float(data["Global Quote"]["05. price"])
        return price
    except Exception:
        return None

wolfram_client = None
if WOLFRAM_APP_ID and not WOLFRAM_APP_ID.startswith("YOUR_"):
    try:
        wolfram_client = wolframalpha.Client(WOLFRAM_APP_ID)
    except Exception as e:
        print("Wolfram init error:", e)
        wolfram_client = None

def query_wolfram(query):
    if wolfram_client is None:
        speak("Wolfram client not configured.")
        return ""
    try:
        res = wolfram_client.query(query)
        ans = next(res.results).text
        speak(ans)
        return ans
    except Exception as e:
        print("wolfram error:", e)
        speak("No result from Wolfram.")
        return ""
# ------------------------------------------------------------------------------

# --------------------------- GUI and threads --------------------------------
class JarvisApp:
    def __init__(self, root):
        self.root = root
        root.title("Jarvis — Voice Assistant")
        root.geometry("820x520")
        root.resizable(False, False)

        # Left panel - controls
        left = tk.Frame(root, width=300, padx=10, pady=10)
        left.pack(side="left", fill="y")

        tk.Label(left, text="Jarvis Dashboard", font=("Helvetica", 16, "bold")).pack(pady=6)
        tk.Button(left, text="🎤 Listen (Voice)", width=26, command=self.thread(self.cmd_listen)).pack(pady=4)
        tk.Button(left, text="🔎 Wikipedia", width=26, command=self.thread(self.cmd_wikipedia)).pack(pady=4)
        tk.Button(left, text="📰 Top News", width=26, command=self.thread(self.cmd_news)).pack(pady=4)
        tk.Button(left, text="☁ Weather", width=26, command=self.thread(self.cmd_weather)).pack(pady=4)
        tk.Button(left, text="🧮 WolframAlpha", width=26, command=self.thread(self.cmd_wolfram)).pack(pady=4)
        tk.Button(left, text="▶ Play on YouTube", width=26, command=self.thread(self.cmd_play_youtube)).pack(pady=4)
        tk.Button(left, text="📸 Capture Photo", width=26, command=self.thread(self.cmd_capture_photo)).pack(pady=4)
        tk.Button(left, text="📷 Screenshot", width=26, command=self.thread(self.cmd_screenshot)).pack(pady=4)
        tk.Button(left, text="📂 PDF Reader", width=26, command=self.thread(self.cmd_pdf)).pack(pady=4)
        tk.Button(left, text="📨 Send SMS (Vonage)", width=26, command=self.thread(self.cmd_send_sms)).pack(pady=4)
        tk.Button(left, text="💹 Stock Price", width=26, command=self.thread(self.cmd_stock)).pack(pady=4)
        tk.Button(left, text="⚠ Shutdown PC", width=26, command=self.cmd_shutdown).pack(pady=6)
        tk.Button(left, text="❌ Exit Jarvis", width=26, command=self.cmd_exit).pack(pady=2)

        # Right panel - logs
        right = tk.Frame(root, padx=10, pady=10)
        right.pack(side="right", expand=True, fill="both")

        tk.Label(right, text="Activity Log", font=("Helvetica", 14)).pack()
        self.log = tk.Text(right, state="disabled", wrap="word")
        self.log.pack(expand=True, fill="both", padx=6, pady=6)

        # Welcome and wish in background
        self.log_message("Jarvis initialized.")
        threading.Thread(target=wish_me, daemon=True).start()

    # Utility: threaded wrapper
    def thread(self, fn):
        def wrapper(*a, **kw):
            def run():
                try:
                    self.log_message(f"Running: {fn.__name__}")
                    fn(*a, **kw)
                    self.log_message(f"Done: {fn.__name__}")
                except Exception as e:
                    self.log_message(f"Error in {fn.__name__}: {e}")
            threading.Thread(target=run, daemon=True).start()
        return wrapper

    def log_message(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")
        print(msg)

    # ---------------- commands (wrappers) -----------------
    def cmd_listen(self):
        self.log_message("Listening for voice command...")
        txt = listen_once()
        if not txt:
            self.log_message("No voice input detected.")
            speak("I did not hear anything.")
            return
        self.log_message(f"Heard: {txt}")
        speak(f"You said: {txt}")

        # basic direct handling
        if "wikipedia" in txt:
            q = txt.replace("wikipedia", "").strip()
            res = search_wikipedia(q or txt)
            self.log_message(res[:800] if res else "No wiki result")
        elif "time" in txt:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_message(f"Time: {t}")
            speak(f"The time is {t}")
        elif "news" in txt:
            self.cmd_news()
        elif "weather" in txt:
            # ask for city
            speak("Which city?")
            city = listen_once()
            if city:
                w = get_weather(city)
                if w:
                    s = f"{city}: {w['temp']}°C, {w['desc']}, humidity {w['humidity']}%"
                    self.log_message(s)
                    speak(s)
                else:
                    speak("Couldn't find weather for that city.")
        elif "wolfram" in txt or any(w in txt for w in ("calculate","solve","what is","who is","integrate","differentiate")):
            self.cmd_wolfram(query=txt)
        elif "youtube" in txt or "play" in txt:
            self.cmd_play_youtube(prompt=txt)
        else:
            self.log_message("No automatic action found for voice command.")

    def cmd_wikipedia(self):
        q = simpledialog.askstring("Wikipedia", "Search Wikipedia for:")
        if not q:
            return
        self.log_message(f"Wikipedia search: {q}")
        res = search_wikipedia(q)
        self.log_message(res[:1000] + ("..." if len(res) > 1000 else ""))

    def cmd_news(self):
        self.log_message("Fetching top news...")
        get_news()

    def cmd_weather(self):
        city = simpledialog.askstring("Weather", "City name:")
        if not city:
            return
        w = get_weather(city)
        if w:
            s = f"{city}: {w['temp']}°C, {w['desc']}, humidity {w['humidity']}%"
            self.log_message(s)
            speak(s)
        else:
            self.log_message("Weather not found.")
            speak("Weather not found.")

    def cmd_wolfram(self, query=None):
        if not query:
            query = simpledialog.askstring("WolframAlpha", "Enter question or expression:")
            if not query:
                return
        self.log_message(f"Wolfram query: {query}")
        res = query_wolfram(query)
        self.log_message(res[:1000] if res else "No Wolfram result.")

    def cmd_play_youtube(self, prompt=None):
        if not prompt:
            prompt = simpledialog.askstring("YouTube", "Enter video / song to play:")
            if not prompt:
                return
        self.log_message(f"Playing on YouTube: {prompt}")
        play_on_youtube(prompt)

    def cmd_capture_photo(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", title="Save photo as...", initialdir=str(SCREENSHOT_DIR))
        if not path:
            path = None
        p = capture_photo(Path(path) if path else None)
        if p:
            self.log_message(f"Photo saved: {p}")

    def cmd_screenshot(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", title="Save screenshot as...", initialdir=str(SCREENSHOT_DIR))
        if not path:
            path = None
        p = take_screenshot(Path(path) if path else None)
        self.log_message(f"Screenshot saved: {p}")

    def cmd_pdf(self):
        path = filedialog.askopenfilename(title="Choose PDF", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        page = simpledialog.askinteger("PDF Reader", "Page number (0-index):", minvalue=0, initialvalue=0)
        txt = read_pdf(path, page or 0)
        self.log_message(txt[:800] + ("..." if len(txt) > 800 else ""))

    def cmd_send_sms(self):
        to = simpledialog.askstring("Send SMS", "Recipient number (with country code):")
        text = simpledialog.askstring("Send SMS", "Message text:")
        if not to or not text:
            return
        ok = send_sms_vonage("Jarvis", to, text)
        self.log_message(f"SMS send result: {ok}")

    def cmd_stock(self):
        symbol = simpledialog.askstring("Stock", "Enter ticker symbol (e.g., AAPL):")
        if not symbol:
            return
        price = get_stock_price(symbol.upper())
        if price:
            txt = f"{symbol.upper()} price: {price}"
            speak(txt)
            self.log_message(txt)
        else:
            self.log_message("Stock price not found.")
            speak("Stock price not found.")

    def cmd_shutdown(self):
        confirm = messagebox.askyesno("Shutdown", "Are you sure you want to shutdown the PC?")
        if confirm:
            speak("Shutting down. Goodbye.")
            if sys.platform == "win32":
                os.system("shutdown /s /t 1")
            elif sys.platform.startswith("linux"):
                os.system("shutdown now")
            else:
                speak("Shutdown not supported on this platform.")

    def cmd_exit(self):
        speak("Goodbye. Jarvis is exiting.")
        self.root.quit()

# ------------------------------------------------------------------------------

def main():
    root = tk.Tk()
    app = JarvisApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
