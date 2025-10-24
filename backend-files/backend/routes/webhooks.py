from flask import Blueprint, request, jsonify

webhook_bp = Blueprint("webhook_bp", __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    # Process the webhook data here
    print(f"Received webhook data: {data}")
    return jsonify({"status": "success"}), 200


