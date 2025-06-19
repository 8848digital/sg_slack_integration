import frappe
import requests
import json
import hmac
import hashlib
import time
import openai


from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id


@frappe.whitelist(allow_guest=True)
def handle_slack_events():
    # # Verify Slack request
    # if not verify_slack_request():
    #     frappe.response["status_code"] = 401
    #     return {"error": "Invalid Slack request"}

    payload = frappe.request.get_data(as_text=True)
    event_data = json.loads(payload)

    # Handle URL verification challenge
    if event_data.get("type") == "url_verification":
        return {"challenge": event_data.get("challenge")}
    setting = frappe.get_cached_doc("Slack Integration Settings")
    # Process message events
    if event_data.get("type") == "event_callback":
        event = event_data.get("event")
        frappe.log_error("AI event data", json.dumps(event, indent=2))
        if event.get("type") in ["message.channels", "message.im", "message"] and not event.get("bot_id"):
            channel = event.get("channel")
            user_message = event.get("text")
            user_id = event.get("user")
            thread_ts = event.get("ts")
            # thread_ts = event.get("channel_id")
            bot_token = setting.project_details_token
            response_text = "⏳ Processing your request... You'll receive a response shortly."
            if str(setting.project_channel_id) != str(channel):
                response_text = "You can only ask this to the Project Info App directly as a message"
            # Acknowledge immediately
            frappe.response["status_code"] = 200
            frappe.response["type"] = "json"
            frappe.response["data"] = response_text

            # Process asynchronously
            frappe.enqueue(
                "sg_slack_integration.doc_events.project_details.process_project_info",
                queue="short",
                job_name="fetch_project_details",
                is_async=True,
                channel=channel,
                user_message=user_message,
                user_id=user_id,
                thread_ts=thread_ts,
                bot_token=bot_token
            )
    return frappe.response["data"]


# def verify_slack_request():
#     signing_secret = frappe.get_site_config().get("slack_signing_secret")
#     timestamp = frappe.request.headers.get("X-Slack-Request-Timestamp")
#     request_body = frappe.request.get_data().decode("utf-8")
#     sig_basestring = f"v0:{timestamp}:{request_body}"
#     computed_sig = "v0=" + hmac.new(
#         signing_secret.encode(),
#         sig_basestring.encode(),
#         hashlib.sha256
#     ).hexdigest()
#     slack_sig = frappe.request.headers.get("X-Slack-Signature")
#     return hmac.compare_digest(computed_sig, slack_sig)


def process_project_info(channel, user_message, user_id, thread_ts, bot_token):
    setting = frappe.get_cached_doc("Slack Integration Settings")
    # Check if command is enabled (based on your previous message)
    if not is_command_enabled():
        send_slack_response(
            channel, thread_ts, bot_token,
            "🚨 Project Detail functionality is disabled in Slack Integration Settings. Kindly enable it under Project Detail AI Tab. ⚙️"
        )
        return
    frappe.log_error("AI slack command enabled")
    # Lookup Slack user_id -> ERPNext email
    slack_user_email = get_email_id_from_slack_user_id(user_id)
    if not slack_user_email:
        send_slack_response(
            channel, thread_ts, bot_token,
            "⚠️ Could not identify you in ERP system."
        )
        return
    frappe.log_error("AI user found")
    # Check if user has role
    allowed_roles = [each.role for each in setting.project_allowed_roles]
    user_roles = frappe.get_roles(slack_user_email)
    # Check if user has at least one allowed role
    has_permission = any(role in allowed_roles for role in user_roles)

    if not has_permission:  # Fixed role name to match error message
        send_slack_response(
            channel, thread_ts, bot_token,
            "🚫 You do not have permission to query project details. Partner role required."
        )
        return
    frappe.log_error("AI has role")
    # Use OpenAI to interpret the request
    # project_detail = interpret_request_with_openai(user_message)
    # if not project_detail:
    #     send_slack_response(
    #         channel, thread_ts, bot_token,
    #         "🤔 Sorry, I couldn't understand your request. Please specify the project and details needed (e.g., status, budget, deadline). ❓"
    #     )
    #     return

    # Query Frappe ERP
    # project_id = project_detail.get("project_id")
    # detail_type = project_detail.get("detail_type")
    project_id = "PROJ-1224"
    detail_type = "status"
    response_text = query_erp_project(project_id, detail_type)
    frappe.log_error("AI Project details for erp", str(response_text))

    # Send response to Slack
    send_slack_response(channel, thread_ts, bot_token, response_text)


def is_command_enabled():
    # Check if the command is enabled in a custom DocType or Site Config
    # Example: Check a custom "Slack Integration Settings" DocType
    settings = frappe.get_cached_doc("Slack Integration Settings")
    return settings.project_enable


def interpret_request_with_openai(message):
    settings = frappe.get_cached_doc("Slack Integration Settings")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.project_ai_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that interprets user requests for project details from an ERP system. "
                        "Extract the project ID (or name) and the specific detail(s) requested (e.g., status, budget, deadline, members, or 'all' for all details). "
                        "If multiple details are requested, return them as a list. If the user asks for everything, return 'all'. "
                        "Return a JSON object with 'project_id' and 'detail_type'. If unclear, return an empty object."
                    )
                },
                {"role": "user", "content": message}
            ],
            max_tokens=100
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        frappe.log_error(f"OpenAI Error: {str(e)}")
        return {}

def query_erp_project(project_id, detail_type):
    try:
        # Query the Project DocType
        project = frappe.get_doc("Project", {"name": project_id})
        if not project:
            return "❌ Project not found. Please check the project ID. 🔍"

        # Define available project details
        detail_map = {
            "status": f"📊 Project Status: {project.status}",
            # "budget": f"💰 Project Budget: {project.total_cost or 'Not set'}",
            # "deadline": f"⏰ Project Deadline: {project.expected_end_date or 'Not set'}",
            # "members": f"👥 Project Members: {', '.join([m.user for m in project.project_users]) or 'None'}"
        }

        # Handle different detail_type inputs
        if detail_type == "all" or not detail_type:
            # Return all details as a formatted string
            response = "\n".join([detail_map[key] for key in detail_map])
        elif isinstance(detail_type, list):
            # Handle multiple details (e.g., ["status", "budget"])
            valid_details = [detail_map.get(
                dt, f"🤔 Unknown detail: {dt}. Try status, budget, deadline, or members. ❓") for dt in detail_type]
            response = "\n".join(valid_details)
        else:
            # Handle single detail
            response = detail_map.get(
                detail_type, f"🤔 Unknown detail requested: {detail_type}. Try status, budget, deadline, or members. ❓")

        return response
    except Exception as e:
        frappe.log_error(f"ERP Query Error: {str(e)}")
        return "⚠️ Error retrieving project details. Please try again later. 🛠️"


def send_slack_response(channel, thread_ts, bot_token, text):
    slack_url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {bot_token}",
               "Content-Type": "application/json"}
    # Split text into chunks of 2900 characters to stay under limit
    chunks = [text[i:i+2900] for i in range(0, len(text), 2900)]
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": chunk}}
              for chunk in chunks]
    payload = {
        "channel": channel,
        "thread_ts": thread_ts,
        "blocks": blocks,
        "response_type": "in_channel"
    }
    try:
        response = requests.post(
            slack_url, json=payload, headers=headers, timeout=5)
        if not response.json().get("ok"):
            frappe.log_error(f"Slack Response Error: {response.json()}")
    except Exception as e:
        frappe.log_error(f"Slack Send Error: {str(e)}")
