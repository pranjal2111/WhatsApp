# bot/views.py

import os
import json
import requests
from dotenv import load_dotenv
from django.http import HttpResponse
from .data import SERVICES

load_dotenv()  # ✅ Load .env variables

VERIFY_TOKEN = "test123"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


PAGE_BUTTONS = {
    "page_1": [
        {"id": "1", "title": "1. BINN ANAMAT"},
        {"id": "2", "title": "2. DOMICILE CERT"},
        {"id": "3", "title": "3. WIDOW ASSIST"},
        {"id": "next_2", "title": "➡️ Next"}
    ],
    "page_2": [
        {"id": "4", "title": "4. INCOME CERT"},
        {"id": "5", "title": "5. GIRL CHILD"},
        {"id": "6", "title": "6. RTE"},
        {"id": "prev_1", "title": "⬅️ Prev"},
        {"id": "next_3", "title": "➡️ Next"}
    ],
    "page_3": [
        {"id": "7", "title": "7. EWS"},
        {"id": "8", "title": "8. SR. CITIZEN"},
        {"id": "9", "title": "9. GUARDIAN"},
        {"id": "prev_2", "title": "⬅️ Prev"},
        {"id": "next_4", "title": "➡️ Next"}
    ],
    "page_4": [
        {"id": "10", "title": "10. INHERITANCE"},
        {"id": "11", "title": "11. CASTE CERT"},
        {"id": "12", "title": "12. MARRIAGE REG"},
        {"id": "prev_3", "title": "⬅️ Prev"},
        {"id": "next_5", "title": "➡️ Next"}
    ],
    "page_5": [
        {"id": "13", "title": "13. NON-CRIMINAL"},
        {"id": "14", "title": "14. SCHOLARSHIP"},
        {"id": "15", "title": "15. SEPARATE COUPON"},
        {"id": "prev_4", "title": "⬅️ Prev"},
        {"id": "next_6", "title": "➡️ Next"}
    ],
    "page_6": [
        {"id": "16", "title": "16. SATYAVADI ASSIST"},
        {"id": "17", "title": "17. DOCUMENTS SUBMITTED"},
        {"id": "18", "title": "18. INHERITANCE 7/12"},
        {"id": "prev_5", "title": "⬅️ Prev"},
        {"id": "next_7", "title": "➡️ Next"}
    ],
    "page_7": [
        {"id": "19", "title": "19. MARRIAGE REG"},
        {"id": "20", "title": "20. SCHOLARSHIP"},
        {"id": "prev_6", "title": "⬅️ Prev"}
    ]
}

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
    requests.post(url, headers=headers, json=payload)

def send_button_page(recipient_id, page="page_1"):
    buttons = PAGE_BUTTONS.get(page, PAGE_BUTTONS["page_1"])
    formatted_buttons = [
        {
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"]
            }
        }
        for btn in buttons[:3]
    ]
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "📑 Please choose a service:"},
            "action": {"buttons": formatted_buttons}
        }
    }
    requests.post(url, headers=headers, json=payload)

def webhook(request):
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)  # ✅ Fixed line
        return HttpResponse("Token mismatch", status=403)


    elif request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        try:
            messages = data['entry'][0]['changes'][0]['value'].get('messages', [])
            if messages:
                msg = messages[0]
                sender = msg['from']
                text = msg.get('text', {}).get('body', '').strip().lower()

                # Handle text commands
                if text in ["menu", "start", "help"]:
                    send_button_page(sender, "page_1")
                    return HttpResponse("EVENT_RECEIVED", status=200)

                # Handle button reply
                if msg.get("type") == "interactive":
                    button_id = msg["interactive"]["button_reply"]["id"]
                    if button_id.startswith("next_"):
                        send_button_page(sender, f"page_{button_id[-1]}")
                    elif button_id.startswith("prev_"):
                        send_button_page(sender, f"page_{button_id[-1]}")
                    elif button_id in SERVICES:
                        service = SERVICES[button_id]
                        reply = f"*{service['title']}*\nDocuments:\n" + "\n".join(f"• {doc}" for doc in service["documents"])
                        send_whatsapp_message(sender, reply)
                    else:
                        send_whatsapp_message(sender, "❌ Invalid option.")
        except Exception as e:
            print("Webhook error:", str(e))

        return HttpResponse("EVENT_RECEIVED", status=200)

    return HttpResponse("Only GET/POST supported", status=405)
