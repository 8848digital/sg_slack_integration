import frappe
import requests
import json

SLACK_BOT_TOKEN = frappe.db.get_single_value("Slack Settings", "issue_token")  # store securely

@frappe.whitelist(allow_guest=True)
def create_dialog_slack():
    req = frappe.request
    data = req.form  # Slack sends form data, not JSON
    frappe.log_error('Received Data',data)
    trigger_id = data.get("trigger_id")
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")
    # frappe.log_error('Data',data)
    # Immediately respond to Slack within 3s (required)
    frappe.response["type"] = "plain"
    frappe.response["message"] = ""   # just empty response (modal opens separately)

    # Open the modal asynchronously
    open_modal(trigger_id, user_id, channel_id)


def open_modal(trigger_id, user_id, channel_id):
    try:
        """Open Slack modal using views.open API"""
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-type": "application/json"
        }

        modal_view = {
            "type": "modal",
            "callback_id": "create_issue_modal",
            "title": {"type": "plain_text", "text": "Create Issue"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "private_metadata": json.dumps({"channel_id": channel_id, "user_id": user_id}),
            "blocks": [
                {
                    "type": "input",
                    "block_id": "subject_block",
                    "label": {"type": "plain_text", "text": "Subject"},
                    "element": {"type": "plain_text_input", "action_id": "subject_input"}
                },
                {
                    "type": "input",
                    "block_id": "priority_block",
                    "label": {"type": "plain_text", "text": "Priority"},
                    "element": {
                        "type": "static_select",
                        "action_id": "priority_input",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Low"}, "value": "Low"},
                            {"text": {"type": "plain_text", "text": "Medium"}, "value": "Medium"},
                            {"text": {"type": "plain_text", "text": "High"}, "value": "High"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "category_block",
                    "label": {"type": "plain_text", "text": "Issue Category"},
                    "element": {"type": "plain_text_input", "action_id": "category_input"}
                },
                {
                    "type": "input",
                    "block_id": "type_block",
                    "label": {"type": "plain_text", "text": "Issue Type"},
                    "element": {"type": "plain_text_input", "action_id": "type_input"}
                },
                {
                    "type": "input",
                    "block_id": "desc_block",
                    "label": {"type": "plain_text", "text": "Description"},
                    "element": {"type": "plain_text_input", "action_id": "desc_input", "multiline": True}
                }
            ]
        }

        payload = {
            "trigger_id": trigger_id,
            "view": modal_view
        }

        r = requests.post("https://slack.com/api/views.open", headers=headers, data=json.dumps(payload))
        frappe.log_error('response value',r.json())
        if not r.json().get("ok"):
            frappe.log_error(f"Slack modal open failed: {r.text}")
    except Exception as e:
        frappe.log_error('Open Modal',e)