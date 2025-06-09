import os
import json
import requests
from dotenv import load_dotenv
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .data import SERVICES

# .env વેરિએબલ્સ લોડ કરો
load_dotenv()
VERIFY_TOKEN = "123"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# કેટેગરી ક્લાસિફિકેશન (મેન્યુઅલી)
CATEGORY_SERVICES = {
    "cat_dakhalo": ["1", "2", "4", "10", "11", "13", "14"],
    "cat_online": ["12", "6", "20"],
    "cat_sahay": ["3", "5", "7", "8", "9", "15", "16", "17"],
    "cat_other": ["18", "19"]
}

CATEGORIES = [
    {"id": "cat_dakhalo", "title": "1. દાખલો"},
    {"id": "cat_online", "title": "2. ઓનલાઇન ફોર્મ"},
    {"id": "cat_sahay", "title": "3. સહાય"},
    {"id": "cat_other", "title": "4. અન્ય સેવાઓ"}
]

# ટેક્સ્ટ મોકલવાનું

def send_whatsapp_message(recipient_id, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📨 Text Response:", response.status_code, response.text)

# કેટેગરી ઓપ્શન બતાવવું

def send_category_options(recipient_id):
    for i in range(0, len(CATEGORIES), 3):
        buttons = [
            {
                "type": "reply",
                "reply": {"id": btn["id"], "title": btn["title"]}
            }
            for btn in CATEGORIES[i:i + 3]
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "📂 કૃપા કરીને કેટેગરી પસંદ કરો:"},
                "action": {"buttons": buttons}
            }
        }

        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload)
        print("📨 Category Response:", response.status_code, response.text)

# કેટેગરી મુજબ સર્વિસ બતાવવી

def send_services_for_category(recipient_id, category_id):
    service_ids = CATEGORY_SERVICES.get(category_id, [])
    for i in range(0, len(service_ids), 3):
        chunk = service_ids[i:i + 3]
        buttons = []
        for sid in chunk:
            service = SERVICES.get(sid)
            if service:
                buttons.append({
                    "type": "reply",
                    "reply": {"id": sid, "title": service["title"][:20]}
                })

        if not buttons:
            continue

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "🧾 કૃપા કરીને સેવા પસંદ કરો:"},
                "action": {"buttons": buttons}
            }
        }

        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=payload)
        print("📨 Service Btn Response:", response.status_code, response.text)

# webhook view
@csrf_exempt
def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse("Unauthorized", status=403)

    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("🔥 ઇનપુટ ડેટા:", json.dumps(data, indent=2))

            try:
                entry = data.get('entry', [])[0]
                changes = entry.get('changes', [])[0]
                value = changes.get('value', {})
                messages = value.get('messages', [])
            except Exception as e:
                print("❌ JSON structure mismatch:", str(e))
                return HttpResponse("Bad JSON", status=400)

            if messages:
                msg = messages[0]
                sender = msg['from']

                if msg.get("type") == "text":
                    text = msg["text"].get("body", "").strip().lower()
                    if text in ["hi", "hello", "હાય", "help", "menu"]:
                        send_whatsapp_message(sender, "🙏 નમસ્તે! આપનું સ્વાગત છે.")
                        send_category_options(sender)
                    else:
                        send_whatsapp_message(sender, "ℹ️ કૃપા કરીને 'hi' લખી શરૂ કરો.")

                interactive = msg.get("interactive")
                if interactive and interactive.get("type") == "button_reply":
                    button_id = interactive["button_reply"]["id"]

                    if button_id.startswith("cat_"):
                        send_services_for_category(sender, button_id)
                    elif button_id in SERVICES:
                        service = SERVICES[button_id]
                        docs = "\n".join(f"• {doc}" for doc in service["documents"])
                        reply = f"*{service['title']}*\n📋 જરૂરી દસ્તાવેજો:\n{docs}"
                        send_whatsapp_message(sender, reply)
                    else:
                        send_whatsapp_message(sender, "❌ માન્ય વિકલ્પ મળ્યો નથી.")

        except Exception as e:
            print("🚨 Webhook Error:", str(e))

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("માત્ર GET/POST આધારભૂત છે", status=405)
