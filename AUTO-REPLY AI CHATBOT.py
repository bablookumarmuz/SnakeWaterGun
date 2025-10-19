"""
AUTO-REPLY AI CHATBOT (Updated, Safe + Test Mode)

Features:
- Uses pyautogui + pyperclip to copy chat text and paste replies.
- Uses OpenAI ChatCompletion (gpt-3.5-turbo) if OPENAI_API_KEY is set.
- If OPENAI_API_KEY is NOT set or OPENAI_TEST_MODE=1, runs in MOCK mode returning safe canned replies so you can test without a key.
- Includes coordinate helper, logging, duplicate handling, and basic profanity checks.
- DOES NOT include any real API keys. You must provide your own key via environment variable.

How to use (PowerShell):
1) To run in real mode (temporary for session):
   $env:OPENAI_API_KEY="sk-..."            # replace with your key (do NOT share it)
   python "AUTO-REPLY AI CHATBOT.py"

2) To run in test/mock mode (no key needed):
   $env:OPENAI_TEST_MODE="1"
   python "AUTO-REPLY AI CHATBOT.py"

3) To set persistent user env var in PowerShell (optional):
   [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "User")

Dependencies:
 pip install pyautogui pyperclip openai

IMPORTANT SAFETY:
- Do NOT use to harass or target named private individuals.
- Use only in chats where you have permission.
"""

import os
import time
import pyautogui
import pyperclip
import re
import sys
import random
from datetime import datetime

# Try to import openai only if available
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    pass

# ---------------- CONFIG ----------------
# Coordinates: replace these after running positions_helper()
CHAT_SELECT_START = (300, 300)
CHAT_SELECT_END   = (1200, 1200)
CHAT_INPUT_POS = (900, 1270)
CHAT_URL = None  # set to web chat URL like "https://web.whatsapp.com/" or None
OPEN_DELAY = 6
CHECK_INTERVAL = 7
DRAG_DURATION = 0.6
BOT_NAME = "Naruto"
TRIGGER_KEYWORDS = ["naruto", "bot", "hey naruto", "@naruto"]
MAX_MESSAGE_CHARS = 3000
PROFANITY_PATTERNS = [r"\b(shit|fuck|bitch|asshole|cunt)\b"]
# ----------------------------------------

def get_env(name, default=None):
    v = os.getenv(name)
    if v is None:
        return default
    return v

# Determine mode: real vs mock
OPENAI_API_KEY = get_env("OPENAI_API_KEY", None)
OPENAI_TEST_MODE = get_env("OPENAI_TEST_MODE", "0") == "1"

if OPENAI_API_KEY and OPENAI_AVAILABLE:
    openai.api_key = OPENAI_API_KEY
    MODE = "REAL"
elif OPENAI_TEST_MODE:
    MODE = "MOCK"
else:
    # If openai library missing but user provided key, warn and use MOCK
    if OPENAI_API_KEY and not OPENAI_AVAILABLE:
        print("[WARN] openai library not installed or failed to import. Starting in MOCK mode.")
    MODE = "MOCK"

# ---------------- Utilities ----------------

def positions_helper():
    input("Move mouse to TOP-LEFT of chat area and press Enter...")
    tl = pyautogui.position()
    print("Top-left:", tl)
    input("Move mouse to BOTTOM-RIGHT of chat area and press Enter...")
    br = pyautogui.position()
    print("Bottom-right:", br)
    input("Move mouse to CHAT INPUT box and press Enter...")
    inp = pyautogui.position()
    print("Chat input:", inp)
    print("\nUse these values in the script (replace constants):")
    print(f"CHAT_SELECT_START = ({tl.x}, {tl.y})")
    print(f"CHAT_SELECT_END   = ({br.x}, {br.y})")
    print(f"CHAT_INPUT_POS    = ({inp.x}, {inp.y})")

def safe_sleep(seconds):
    try:
        for _ in range(int(seconds)):
            time.sleep(1)
        rem = seconds - int(seconds)
        if rem > 0:
            time.sleep(rem)
    except KeyboardInterrupt:
        print("Interrupted by user.")
        sys.exit(0)

# ---------------- Chat Interaction ----------------

def open_chat():
    if CHAT_URL:
        import webbrowser
        webbrowser.open(CHAT_URL)
        print(f"[{datetime.now()}] Opened {CHAT_URL}. Waiting {OPEN_DELAY}s...")
        safe_sleep(OPEN_DELAY)
    else:
        print(f"[{datetime.now()}] CHAT_URL not set; ensure chat app is visible.")
        safe_sleep(1.5)

def copy_chat_text():
    sx, sy = CHAT_SELECT_START
    ex, ey = CHAT_SELECT_END
    pyautogui.moveTo(sx, sy, duration=0.3)
    pyautogui.dragTo(ex, ey, duration=DRAG_DURATION, button='left')
    safe_sleep(0.25)
    pyautogui.hotkey('ctrl', 'c')
    safe_sleep(0.25)
    text = pyperclip.paste()
    if not text:
        print("[WARN] Clipboard empty after copy — check coordinates or increase delays.")
    return text

def paste_and_send(text):
    pyautogui.click(*CHAT_INPUT_POS)
    safe_sleep(0.15)
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')
    safe_sleep(0.12)
    pyautogui.press('enter')
    print(f"[{datetime.now()}] Sent: {text[:120]}{'...' if len(text)>120 else ''}")

# ---------------- Analysis ----------------

def extract_last_sender_and_message(chat_text):
    if not chat_text:
        return None, None
    lines = [ln.strip() for ln in chat_text.strip().splitlines() if ln.strip()]
    if not lines:
        return None, None
    last = lines[-1]
    # Try "Name: message"
    if ":" in last:
        parts = last.split(":", 1)
        sender = parts[0].strip()
        message = parts[1].strip()
        return sender, message
    # Try alternate pattern
    if len(lines) >= 2:
        candidate_sender = lines[-2]
        candidate_message = lines[-1]
        if len(candidate_sender) < 40 and len(candidate_message) > 0:
            return candidate_sender, candidate_message
    return None, last

def should_respond(sender, message):
    if not message:
        return False
    lower = message.lower()
    for kw in TRIGGER_KEYWORDS:
        if kw in lower:
            return True
    if lower.endswith('?') or lower.endswith('!'):
        return True
    # Chance-based short responses to casual lines
    if random.random() < 0.06:
        return True
    return False

def contains_profanity(text):
    if not text:
        return False
    for pat in PROFANITY_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False

# ---------------- OpenAI / Mock ----------------

def mock_generate_naruto_reply(chat_history, last_sender, last_message):
    # A list of safe, playful Naruto-style lines (no personal attacks)
    templates = [
        "Heh, {sender}, you talk big — did you swallow a comic book or what?",
        "Oi {sender}, even ramen needs a break from your drama 🍜",
        "Hands off the spotlight, {sender} — it's my turn to be dramatic!",
        "If boasting burned calories, {sender} you'd be an Olympic athlete 😄",
        "Calm down, {sender}. Save some jokes for the encore!",
        "Nice try, {sender}. That clap was politely surprised 👏",
        "You’re trying, {sender} — points for effort and style.",
    ]
    s = last_sender or "there"
    t = random.choice(templates)
    reply = t.format(sender=s).strip()
    # Keep it short
    if len(reply) > 200:
        reply = reply[:197] + "..."
    return reply

def real_generate_naruto_reply(chat_history, last_sender, last_message):
    """
    Use OpenAI ChatCompletion (gpt-3.5-turbo).
    This function is only used if openai is available and API key provided.
    """
    system = (
        "You are Naruto Uzumaki in a friendly, comedic roast mode. Produce a witty, "
        "light-hearted one- or two-sentence reply. NEVER generate threats, slurs, "
        "sexual content, or personal attacks. If user content would produce abusive content, "
        "refuse and return a friendly joke instead."
    )
    user_prompt = (
        f"Chat excerpt (trimmed):\n{chat_history[:MAX_MESSAGE_CHARS]}\n\n"
        f"Last sender: {last_sender}\n"
        f"Last message: {last_message}\n\n"
        "Produce a single short reply as Naruto (<= 200 chars). Keep it playful and non-abusive."
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.85,
            max_tokens=120,
        )
        text = resp.choices[0].message.content.strip()
        # Safety: if profanity detected, fallback to softening or mock
        if contains_profanity(text) or len(text) > 400:
            return soften_reply(text)
        return text
    except Exception as e:
        print("[ERROR] OpenAI call failed:", e)
        return "Oops — Naruto's brain overloaded 😅"

def soften_reply(reply_text):
    # If openai available try soften, else fallback to a polite canned reply
    if MODE == "REAL" and OPENAI_AVAILABLE:
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that softens tone."},
                    {"role": "user", "content": f"Rewrite to be light-hearted and non-abusive: {reply_text}"}
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print("[WARN] softening via OpenAI failed:", e)
    # Fallback
    return "Haha, that was spicy — but let's keep it friendly 😄"

def generate_naruto_reply(chat_history, last_sender, last_message):
    if MODE == "MOCK":
        return mock_generate_naruto_reply(chat_history, last_sender, last_message)
    else:
        return real_generate_naruto_reply(chat_history, last_sender, last_message)

# ---------------- Main Loop ----------------

def main_loop():
    print(f"Mode: {MODE}. Starting bot. Ctrl-C to stop.")
    open_chat()
    last_handled = None
    while True:
        try:
            chat_text = copy_chat_text()
            sender, message = extract_last_sender_and_message(chat_text)
            print(f"[{datetime.now()}] Parsed -> Sender: {sender!r}, Message: {message!r}")

            key = (sender, message)
            if key == last_handled:
                safe_sleep(CHECK_INTERVAL)
                continue

            if should_respond(sender, message):
                print("Trigger detected — generating reply...")
                reply = generate_naruto_reply(chat_text, sender or "there", message or "")
                # final safety check
                if contains_profanity(reply):
                    print("Profanity found in generated reply; softening...")
                    reply = soften_reply(reply)
                paste_and_send(reply)
                last_handled = key
            else:
                print("No trigger. Sleeping...")
            safe_sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print("[ERROR] Loop exception:", e)
            safe_sleep(3)

# ---------------- Entry ----------------

if __name__ == "__main__":
    print("AUTO-REPLY AI CHATBOT (Updated).")
    print("Coordinates currently set to:\n", CHAT_SELECT_START, CHAT_SELECT_END, CHAT_INPUT_POS)
    print("Mode:", MODE)
    print("If coordinates are wrong, run positions_helper() to capture and paste them into the script.")
    cmd = input("Start bot now? (y/N or type 'help' or 'pos' for helper): ").strip().lower()
    if cmd == 'pos':
        positions_helper()
        print("Run the script again after editing coordinates.")
        sys.exit(0)
    if cmd == 'help':
        print("Set OPENAI_API_KEY environment variable (recommended) or set OPENAI_TEST_MODE=1 for mock mode.")
        print("PowerShell example:\n  $env:OPENAI_TEST_MODE='1'\n  python 'AUTO-REPLY AI CHATBOT.py'")
        sys.exit(0)
    if cmd == 'y':
        main_loop()
    else:
        print("Aborted. Make changes and run again.")
