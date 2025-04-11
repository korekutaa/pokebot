from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import json
import os

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards.json")
DB_FILE_TRAINERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trainers.json")

def load_cards():
    try:
        if not os.path.exists(DB_FILE):
            return {}
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cards(cards):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)

def normalize_id(text):
    return "".join(c for c in text.lstrip("!").lower() if c.isalnum())

def build_response(card):
    response = f"*{card['name']}* [HP]{card['hp']} {card['type']}\n"
    
    if card.get('ability'):
        response += f"\nAbility:\n{card['ability']}\n"
    
    if card.get('attack1'):
        response += f"\n{card['attack1']} {card['damage1']}"
        if card.get('desc1'):
            response += f"\n{card['desc1']}"
    
    if card.get('attack2'):
        response += f"\n\n{card['attack2']} {card['damage2']}"
        if card.get('desc2'):
            response += f"\n{card['desc2']}"
    
    response += f"\n\n*Weakness* {card['weakness']}"
    response += f"\n*Retreat* {card['retreat']}"
    response += f"\n*Rarity* {card['rarity']}"  # Added rarity
    return response

def handle_add_card(parts):
    try:
        if len(parts) < 14:
            return "❌ Format: !addpoke ID|Name|HP|Type|Ability|Attack1|Damage1|Desc1|Attack2|Damage2|Desc2|Weakness|Retreat|Rarity"
        
        card_id = normalize_id(parts[0])
        cards = load_cards()
        
        cards[card_id] = {
            'name': parts[1],
            'hp': parts[2],
            'type': parts[3],
            'ability': parts[4] if parts[4] else None,
            'attack1': parts[5] if parts[5] else None,
            'damage1': parts[6] if parts[6] else None,
            'desc1': parts[7] if parts[7] else None,
            'attack2': parts[8] if parts[8] else None,
            'damage2': parts[9] if parts[9] else None,
            'desc2': parts[10] if parts[10] else None,
            'weakness': parts[11],
            'retreat': parts[12],
            'rarity': parts[13]  # Added rarity
        }
        
        save_cards(cards)
        return f"✅ Added card: {parts[1]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def handle_edit_card(parts):
    try:
        if len(parts) < 3:
            return "❌ Format: !editpoke ID|Field|NewValue\nFields: name, hp, type, ability, attack1-2, damage1-2, desc1-2, weakness, retreat, rarity"
        
        card_id = normalize_id(parts[0])
        field = parts[1].lower()
        new_value = "|".join(parts[2:])
        
        cards = load_cards()
        if card_id not in cards:
            return "❌ Card not found!"
        
        # Updated valid fields
        valid_fields = ['name', 'hp', 'type', 'ability', 'attack1', 'damage1', 
                       'desc1', 'attack2', 'damage2', 'desc2', 'weakness', 
                       'retreat', 'rarity']
        
        if field not in valid_fields:
            return f"❌ Invalid field. Valid fields: {', '.join(valid_fields)}"
        
        cards[card_id][field] = new_value if new_value != "None" else None
        save_cards(cards)
        return f"✅ Updated {field} for {cards[card_id]['name']}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Add trainer database functions
def load_trainers():
    try:
        if not os.path.exists(DB_FILE_TRAINERS):
            return {}
        with open(DB_FILE_TRAINERS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_trainers(trainers):
    with open(DB_FILE_TRAINERS, "w", encoding="utf-8") as f:
        json.dump(trainers, f, indent=2, ensure_ascii=False)

# Add trainer command handlers
def handle_add_trainer(parts):
    try:
        if len(parts) < 5:
            return "❌ Format: !addtrainer ID|Name|Type|Description|Rarity"
        
        trainer_id = normalize_id(parts[0])
        trainers = load_trainers()
        
        trainers[trainer_id] = {
            'name': parts[1],
            'type': parts[2],
            'description': parts[3],
            'rarity': parts[4]
        }
        
        save_trainers(trainers)
        return f"✅ Added trainer: {parts[1]}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def handle_edit_trainer(parts):
    try:
        if len(parts) < 3:
            return "❌ Format: !edittrainer ID|Field|NewValue\nFields: name, type, description, rarity"
        
        trainer_id = normalize_id(parts[0])
        field = parts[1].lower()
        new_value = "|".join(parts[2:])
        
        trainers = load_trainers()
        if trainer_id not in trainers:
            return "❌ Trainer not found!"
        
        valid_fields = ['name', 'type', 'description', 'rarity']
        
        if field not in valid_fields:
            return f"❌ Invalid field. Valid fields: {', '.join(valid_fields)}"
        
        trainers[trainer_id][field] = new_value
        save_trainers(trainers)
        return f"✅ Updated {field} for {trainers[trainer_id]['name']}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Add trainer response builder
def build_response_trainer(trainer):
    return (
        f"*{trainer['name']}* ({trainer['type']})\n"
        f"{trainer['description']}\n"
        f"*Rarity* {trainer['rarity']}"
    )

@app.route("/webhook", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    resp = MessagingResponse()
    
    try:
        if incoming_msg.startswith("!addtrainer"):
            reply = handle_add_trainer(incoming_msg[11:].split("|"))
        elif incoming_msg.startswith("!edittrainer"):
            reply = handle_edit_trainer(incoming_msg[12:].split("|"))
        elif incoming_msg.startswith("!addpoke"):
            reply = handle_add_card(incoming_msg[8:].split("|"))
        elif incoming_msg.startswith("!editpoke"):
            reply = handle_edit_card(incoming_msg[9:].split("|"))
        elif incoming_msg.startswith("!"):
            command = normalize_id(incoming_msg)
            # Check trainers first
            trainers = load_trainers()
            if command in trainers:
                reply = build_response_trainer(trainers[command])
            else:
                # Then check Pokémon
                cards = load_cards()
                card = cards.get(command)
                reply = build_response(card) if card else "❌ Card not found"
        else:
            reply = "❌ Unrecognized command"
    except Exception as e:
        reply = f"❌ Error processing request: {str(e)}"
    
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)