
import frappe
import requests
import json
from frappe.utils.response import build_response

from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id


@frappe.whitelist(allow_guest=True)
def get_info():
    req = frappe.request
    frappe.log_error("UAT payload", req)
    frappe.log_error("UAT Payload 2", req.form)
    text = req.form.get("text")  # Slash command input
    user_id = req.form.get("user_id")  # Slack user ID
    channel_id = req.form.get("channel_id")  # Slack channel ID

    # Enqueue the processing logic to run asynchronously
    frappe.enqueue(
        "sg_slack_integration.doc_events.project_info.process_slack_request",
        queue="short",
        text=text,
        user_id=user_id,
        channel_id=channel_id
    )

    # Return immediate 200 OK response to acknowledge the slash command
    frappe.local.response["http_status_code"] = 200
    frappe.local.response["content_type"] = "application/json"
    frappe.local.response["data"] = json.dumps(
        {"text": "Processing your request"})
    return


def process_slack_request(text, user_id, channel_id):
    # Validate input
    if not text:
        msg_block = [
            {"type": "mrkdwn",
                "text": f"❌ Please provide valid parameters: `/get-info [project-id] [members|project_details]`"}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    parts = text.split()
    if len(parts) != 2:
        msg_block = [
            {"type": "mrkdwn",
                "text": "❌ Usage: `/get-info [project-id] [members|project_details]`"}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    project_id, info_type = parts

    # Lookup Slack user_id -> ERPNext email
    slack_user_email = get_email_id_from_slack_user_id(user_id)
    if not slack_user_email:
        msg_block = [
            {"type": "mrkdwn", "text": f"⚠️ Could not identify you in ERP system."}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    # Check if user has 'Partner' role
    user_roles = frappe.get_roles(slack_user_email)
    if "Partner" not in user_roles:
        msg_block = [
            {"type": "mrkdwn",
                "text": f"🚫 You do not have permission to access project details."}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    # Fetch the project
    if frappe.db.exists("Project", project_id):
        project_doc = frappe.get_doc("Project", project_id)
    else:
        msg_block = [
            {"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    if info_type == "members":
        members = frappe.get_all("Project Employee Distribution Detail", filters={
            "parent": project_id}, fields=["employee_name", "designation", "from_date", "to_date"])
        if not members:
            msg_block = [
                {"type": "mrkdwn", "text": f"ℹ️ No members found for project `{project_id}`."}
            ]
            return send_slack_message(msg_block, user_id, channel_id)
        msg_block = [
            {"type": "mrkdwn",
                "text": f"These are the members found for project `{project_id}`."}
        ]
        for m in members:
            msg_block.append(
                {"type": "mrkdwn",
                    "text": f"{m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')}"}
            )
        return send_slack_message(msg_block, user_id, channel_id)

    elif info_type == "project_details":
        msg_block = [
            {"type": "mrkdwn", "text": f"*Project ID:*\n{project_doc.name}"},
            {"type": "mrkdwn", "text": f"*Project Name:*\n{project_doc.project_name}"},
            {"type": "mrkdwn", "text": f"*Status:*\n{project_doc.status}"},
            {"type": "mrkdwn",
                "text": f"*Expected Start:*\n{project_doc.expected_start_date}"},
            {"type": "mrkdwn", "text": f"*Expected End:*\n{project_doc.expected_end_date}"},
            {"type": "mrkdwn", "text": f"*Customer:*\n{project_doc.customer or 'None'}"}
        ]
        return send_slack_message(msg_block, user_id, channel_id)

    else:
        msg_block = [
            {"type": "mrkdwn",
                "text": "❌ Invalid info type. Use `members` or `project_details`."}
        ]
        return send_slack_message(msg_block, user_id, channel_id)


def send_slack_message(message_block, user_id, channel_id):
    token = frappe.db.get_single_value(
        "Slack Integration Settings", "project_details_token")
    # Prepare the Slack API payload for chat.postEphemeral
    payload = {
        "channel": channel_id,  # Use channel_id for context
        # Ensure the message is ephemeral (visible only to the user)
        "user": user_id,
        "blocks": [
            {
                "type": "section",
                "fields": message_block
            }
        ]
    }

    # Send the message to Slack using chat.postEphemeral
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        "https://slack.com/api/chat.postEphemeral",
        headers=headers,
        data=json.dumps(payload)
    )

    # Log the Slack API response for debugging
    frappe.log_error("Slack API Response", response.text)
    if not (response.status_code == 200 and response.json().get("ok")):
        frappe.log_error("Slack API Error", response.text)
