import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Green API credentials
INSTANCE_ID = os.getenv("INSTANCE_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")
GREEN_API_URL = f"https://7103.api.greenapi.com/waInstance{INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"

app = Flask(__name__)

# Customer ID mapping (Define your customer IDs and phone numbers here)
customer_mapping = {
    "CUST001": "201002143879",
    "CUST002": "201080268815",
}

@app.route('/')
def home():
    return "Flask server is running!", 200

# Function to send a WhatsApp message using customer ID
def send_whatsapp_message(customer_id, message):
    if customer_id not in customer_mapping:
        print(f"Customer ID {customer_id} not found.")
        return

    phone_number = customer_mapping[customer_id]
    chat_id = f"{phone_number}@c.us"
    headers = {"Content-Type": "application/json"}
    payload = {
        "chatId": chat_id,
        "message": message
    }

    try:
        response = requests.post(GREEN_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Message sent successfully to Customer ID {customer_id} ({phone_number}).")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Customer ID {customer_id}: {e}")

# Webhook to handle incoming messages
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        chat_id = data.get('senderData', {}).get('chatId')
        phone_number = chat_id.split('@')[0]

        # Find the customer ID based on the phone number
        customer_id = None
        for cid, pnumber in customer_mapping.items():
            if pnumber == phone_number:
                customer_id = cid
                break

        if not customer_id:
            print(f"Phone number {phone_number} not found in customer mapping.")
            return jsonify({"status": "Customer not found."}), 404

        message_type = data.get('typeMessage')

        if message_type == 'locationMessage':
            latitude = data['messageData'].get('latitude')
            longitude = data['messageData'].get('longitude')
            print(f"Received live location from Customer ID {customer_id}: Latitude={latitude}, Longitude={longitude}")

            send_whatsapp_message(customer_id, "Thank you for sharing your live location!")
            return jsonify({"status": "Location received and processed."}), 200

        else:
            print(f"Received a non-location message from Customer ID {customer_id}. Requesting live location.")
            send_whatsapp_message(customer_id, "We didn't receive a location. Could you please share your live location?")
            return jsonify({"status": "Requested live location."}), 200

    except Exception as e:
        print(f"Error handling webhook: {e}")
        return jsonify({"status": "Error processing the message."}), 500

if __name__ == "__main__":
    # Example: Send a message to a specific customer by their ID
    customer_id = "CUST001"
    message = "Hello! Please share your live location."

    print("Starting Flask server and sending initial message...")
    send_whatsapp_message(customer_id, message)

    # Run the Flask server
    app.run(port=5000)
