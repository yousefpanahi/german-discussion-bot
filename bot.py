import os
import sys
import json
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Your BBC content channel
BBC_CHANNEL_ID = "-1003760493970"


# File that remembers which episode was last sent
COUNTER_FILE = "episode_counter.txt"
EPISODE_MAP_FILE = "episode_message_map.json"

# File that remembers the currently pinned BBC intro message
BBC_PIN_FILE = "bbc_pinned_message_id.txt"


# Tehran timezone
TEHRAN_TZ = ZoneInfo("Asia/Tehran")


# ==================================================
# WAIT UNTIL EXACT SCHEDULED TIME
# ==================================================

def wait_until_target():
    target_time = os.environ.get("TARGET_TEHRAN_TIME")

    # Manual GitHub tests do not provide this variable,
    # so they are sent immediately.
    if not target_time:
        return

    hour, minute = map(int, target_time.split(":"))

    now = datetime.now(TEHRAN_TZ)

    target = now.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0
    )

    # If GitHub was extremely late and the target has already passed,
    # send immediately instead of waiting until the next day.
    if now >= target:
        late_seconds = (now - target).total_seconds()
        print(
            f"Target time already passed by "
            f"{late_seconds:.0f} seconds. Sending now."
        )
        return

    wait_seconds = (target - now).total_seconds()

    print(f"Current Tehran time: {now}")
    print(f"Target Tehran time: {target}")
    print(f"Waiting {wait_seconds:.0f} seconds...")

    time.sleep(wait_seconds)

    print("Target time reached. Sending message.")

# ==================================================
# SEND TELEGRAM MESSAGE
# ==================================================

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    data = response.json()
    print(data)

    if not response.ok:
        raise Exception("Failed to send message")

    return data["result"]["message_id"]

# ==================================================
# PIN TELEGRAM MESSAGE
# ==================================================

def pin_message(message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/pinChatMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "disable_notification": True
        }
    )

    print(response.json())

    if not response.ok:
        raise Exception("Failed to pin message")


# ==================================================
# UNPIN TELEGRAM MESSAGE
# ==================================================

def unpin_message(message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/unpinChatMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "message_id": message_id
        }
    )

    print(response.json())

    if not response.ok:
        raise Exception("Failed to unpin message")


# ==================================================
# BBC PIN STATE
# ==================================================

def save_bbc_pinned_message_id(message_id):
    with open(BBC_PIN_FILE, "w") as file:
        file.write(str(message_id))


def get_bbc_pinned_message_id():
    if not os.path.exists(BBC_PIN_FILE):
        return None

    with open(BBC_PIN_FILE, "r") as file:
        value = file.read().strip()

    if not value:
        return None

    return int(value)


def clear_bbc_pinned_message_id():
    with open(BBC_PIN_FILE, "w") as file:
        file.write("")


# ==================================================
# COPY TELEGRAM MESSAGE
# ==================================================

def copy_message(message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "from_chat_id": BBC_CHANNEL_ID,
            "message_id": message_id
        }
    )

    print(response.json())

    if not response.ok:
        raise Exception(f"Failed to copy message {message_id}")


# ==================================================
# GET CURRENT EPISODE NUMBER
# ==================================================

def get_episode_number():
    if not os.path.exists(COUNTER_FILE):
        return 0

    with open(COUNTER_FILE, "r") as file:
        return int(file.read().strip())

def get_episode_map():
    if not os.path.exists(EPISODE_MAP_FILE):
        raise Exception(
            f"Episode map file not found: {EPISODE_MAP_FILE}"
        )

    with open(EPISODE_MAP_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
        
# ==================================================
# SAVE EPISODE NUMBER
# ==================================================

def save_episode_number(number):
    with open(COUNTER_FILE, "w") as file:
        file.write(str(number))


# ==================================================
# GET QUESTIONS FOR EPISODE
# ==================================================

def get_questions(episode_number):
    filename = f"questions/episode{episode_number:03d}.json"

    if not os.path.exists(filename):
        raise Exception(f"Questions file not found: {filename}")

    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


# ==================================================
# GET VOCABULARY FOR EPISODE
# ==================================================

def get_vocabulary(episode_number):
    filename = f"vocabulary/episode{episode_number:03d}.json"

    if not os.path.exists(filename):
        raise Exception(f"Vocabulary file not found: {filename}")

    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)

# ==================================================
# MESSAGE TYPE
# ==================================================

message_type = os.environ.get("MESSAGE_TYPE")

wait_until_target()

# ==================================================
# 1. CLASS REMINDER
# ==================================================

if message_type == "reminder":

    message = """Hello Everyone. Kindly Reminder

We will have the English Free Discussion meeting today at 4:30 PM - 5:30 PM (UTC)."""

    send_message(message)


# ==================================================
# 2. JOIN CLASS
# ==================================================

elif message_type == "join":

    message = """🔴 LIVE NOW — English Free Discussion 🇬🇧

We’re starting the class now!
Tap the link and join us — we’d love to have you in the discussion. 👋

Even if you’re a few minutes late, just jump in!

🔗 Join the meeting:
https://meet.google.com/vtg-anvk-vgn"""

    # Send the Join Class message
    join_message_id = send_message(message)

    # Pin it immediately
    pin_message(join_message_id)

    print(f"Join message {join_message_id} pinned.")

    # Keep it pinned for 3 hours
    unpin_delay = int(
        os.environ.get("UNPIN_DELAY_SECONDS", "10800")
    )

    print(f"Waiting {unpin_delay} seconds before unpinning.")

    time.sleep(unpin_delay)

    # Unpin only this exact message
    unpin_message(join_message_id)

    print(f"Join message {join_message_id} unpinned.")

# ==================================================
# 3. UNPIN PREVIOUS BBC INTRO
# ==================================================

elif message_type == "bbc_unpin":

    bbc_message_id = get_bbc_pinned_message_id()

    if bbc_message_id is None:
        print("No BBC intro message is currently stored.")
    else:
        unpin_message(bbc_message_id)
        clear_bbc_pinned_message_id()

        print(
            f"BBC intro message {bbc_message_id} "
            f"unpinned successfully."
        )
        

# ==================================================
# 4. BBC 6 MINUTE ENGLISH EPISODE
# ==================================================

elif message_type == "bbc":

    # Get the last episode that was sent
    episode_number = get_episode_number()

    # The next episode
    next_episode = episode_number + 1

    # Load the exact Telegram message IDs for this episode
    episode_map = get_episode_map()

    episode_key = str(next_episode)

    if episode_key not in episode_map:
        raise Exception(
            f"Episode {next_episode} not found in episode map."
        )

    episode_info = episode_map[episode_key]
    message_ids = episode_info["message_ids"]

    print(f"Sending Episode {next_episode}")
    print(f"Message IDs: {message_ids}")

    # Load questions for this episode
    episode_data = get_questions(next_episode)

    title = episode_data["title"]
    questions = episode_data["questions"]

    # Send introduction first
    message = """Hello Guys

The next topic for our free discussion will be the episode below."""

    bbc_intro_message_id = send_message(message)

    # Pin the BBC introduction
    pin_message(bbc_intro_message_id)

    # Remember it so it can be unpinned later
    save_bbc_pinned_message_id(bbc_intro_message_id)

    print(
        f"BBC intro message {bbc_intro_message_id} pinned."
    )

    # Copy description, audio and PDF using exact message IDs
    for message_id in message_ids:
        copy_message(message_id)

    # Discussion introduction
    discussion_message = f"""📚 Discussion Time!

Next Session's Topic: {title}

Please discuss the following questions and try to speak as much as possible.

Remember:
• There are no perfect answers.
• Respect different opinions.
• Help others practice English.

Good luck and enjoy the discussion! 😊"""

    send_message(discussion_message)

    # Send the six questions
    questions_message = "💬 Discussion Questions\n\n"

    for i, question in enumerate(questions, start=1):
        questions_message += f"{i}️⃣ {question}\n\n"

    send_message(questions_message)

    # Only advance after everything succeeded
    save_episode_number(next_episode)

    print(f"Episode {next_episode} completed successfully.")
    

# ==================================================
# 5. EPISODE VOCABULARY
# ==================================================

elif message_type == "vocabulary":

    # The counter contains the most recently sent BBC episode
    episode_number = get_episode_number()

    if episode_number < 1:
        print("No BBC episode has been sent yet.")
        sys.exit(0)

    # Load vocabulary for that episode
    vocabulary_data = get_vocabulary(episode_number)

    title = vocabulary_data["title"]
    vocabulary = vocabulary_data["vocabulary"]

    if len(vocabulary) != 6:
        raise Exception(
            f"Episode {episode_number} must contain exactly 6 vocabulary items."
        )
    
    number_icons = [
        "1️⃣", "2️⃣", "3️⃣",
        "4️⃣", "5️⃣", "6️⃣"
    ]
    
    # Send vocabulary in two messages: 3 words each
    for part in range(2):
    
        start = part * 3
        end = start + 3

        message = (
            f"📌📚📌 Vocabulary Time 📌📚📌\n"
            f"━━━━━━━━━━━━━━\n"
            f"Part {part + 1}/2\n"
            f"Episode {episode_number}: {title}\n\n"
        )
        
        for i in range(start, end):

            item = vocabulary[i]

            message += (
                f"{number_icons[i]} {item['word']}\n"
                f"Meaning: {item['meaning']}\n\n"
                f"🔹 {item['examples'][0]['de']}\n"
                f"   🇬🇧 {item['examples'][0]['en']}\n\n"
                f"🔹 {item['examples'][1]['de']}\n"
                f"   🇬🇧 {item['examples'][1]['en']}\n\n"
            )

        send_message(message)

    print(
        f"Vocabulary for Episode {episode_number} "
        f"sent successfully."
    )

    # After the final episode, restart the full cycle
    if episode_number == 146:
        save_episode_number(0)
        print("Episode 146 completed. Counter reset to 0.")
        
# ==================================================
# INVALID MESSAGE TYPE
# ==================================================

else:

    print("No valid MESSAGE_TYPE was provided.")
    sys.exit(1)
