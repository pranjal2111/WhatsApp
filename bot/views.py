import os
import json
import requests
from dotenv import load_dotenv
from django.http import HttpResponse
from .data import SERVICES
from django.views.decorators.csrf import csrf_exempt

# .env ફાઈલમાંથી વેરિએબલ લોડ કરો
load_dotenv()
VERIFY_TOKEN = "123"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# કેટેગરી વિકલ્પો
CATEGORIES = {
    "category_1": [
        {"id": "cat_dakhalo", "title": "1. દાખલો"},
        {"id": "cat_online", "title": "2. ઓનલાઇન ફોર્મ"},
        {"id": "cat_sahay", "title": "3. સહાય"},
        {"id": "cat_other", "title": "4. અન્ય સેવાઓ"},
    ]
}

# દરેક કેટેગરી મુજબ સર્વિસ બટન વિકલ્પો
CATEGORY_SERVICES = {
    "cat_dakhalo": ["1", "2", "4", "10", "11", "13"],
    "cat_online": ["3", "5", "6", "7", "14", "20"],
    "cat_sahay": ["8", "9", "12", "15", "16"],
    "cat_other": ["17", "18", "19"]
}

# ટેક્સ્ટ મેસેજ મોકલવાનું ફંક્શન
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
    print("📨 ટેક્સ્ટ મોકલાયું:", response.status_code, response.text)

# કેટેગરી વિકલ્પો બતાવવાનું
def send_category_options(recipient_id):
    buttons = CATEGORIES["category_1"]
    for i in range(0, len(buttons), 3):
        chunk = buttons[i:i + 3]
        formatted_buttons = [
            {
                "type": "reply",
                "reply": {"id": btn["id"], "title": btn["title"]}
            }
            for btn in chunk
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": "📂 કૃપા કરીને કેટેગરી પસંદ કરો:"},
                "action": {"buttons": formatted_buttons}
            }
        }

        url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=payload)
        print("📨 કેટેગરી બટન જવાબ:", response.status_code, response.text)

# સેવાઓ બતાવવાનું
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
                    "reply": {
                        "id": sid,
                        "title": service["title"]
                    }
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
        print("📨 સેવા બટન મોકલાયું:", response.status_code, response.text)

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

            messages = data['entry'][0]['changes'][0]['value'].get('messages', [])
            if messages:
                msg = messages[0]
                sender = msg['from']

                # ટેક્સ્ટ મેસેજ હેન્ડલ કરો
                if msg.get("type") == "text":
                    text = msg["text"].get("body", "").strip().lower()
                    if text in ["hi", "menu", "help", "હાય", "મેનુ"]:
                        send_category_options(sender)
                    else:
                        send_whatsapp_message(sender, "ℹ️ કૃપા કરીને 'hi' લખી તમારા વિકલ્પો જુઓ.")

                # બટન રિપ્લાય હેન્ડલ કરો
                interactive = msg.get("interactive")
                if interactive and interactive.get("type") == "button_reply":
                    button_id = interactive["button_reply"]["id"]

                    if button_id.startswith("cat_"):
                        send_services_for_category(sender, button_id)
                    elif button_id in SERVICES:
                        service = SERVICES[button_id]
                        reply = f"*{service['title']}*\n📋 જરૂરી દસ્તાવેજો:\n" + "\n".join(f"• {doc}" for doc in service["documents"])
                        send_whatsapp_message(sender, reply)
                    else:
                        send_whatsapp_message(sender, "❌ અમાન્ય વિકલ્પ.")
        except Exception as e:
            print("🚨 Webhook ભૂલ:", str(e))

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("માત્ર GET/POST આધારભૂત છે", status=405)