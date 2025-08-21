import frappe
import requests
import json
from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id

SLACK_BOT_TOKEN = frappe.db.get_single_value("Slack Integration Settings", "issue_token")  # store securely

@frappe.whitelist(allow_guest=True)
def create_dialog_slack():
    req = frappe.form_dict
    frappe.log_error('Slack Data',req)
    token=req.get('token')
    team_id=req.get('team_id')
    channel_id=req.get('channel_id')
    user_id=req.get('user_id')
    user_name=req.get('user_name')
    command=req.get('command')
    api_app_id=req.get('api_app_id')
    response_url=req.get('response_url')
    trigger_id=req.get('trigger_id')

    frappe.response["type"] = "plain"
    frappe.response["message"] = ""   # just empty response (modal opens separately)

    # Open the modal asynchronously
    open_modal(trigger_id, user_id, channel_id)

@frappe.whitelist(allow_guest=True)
def open_modal(trigger_id, user_id, channel_id):
    try:
        # Fetch Issue Category options from Issue doctype field

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
                    "element": {
                        "type": "static_select",
                        "action_id": "category_input",
                        "options": [
                            {"text": {"type": "plain_text", "text": "HR"}, "value": "HR"},
                            {"text": {"type": "plain_text", "text": "Finance Team Support"}, "value": "Finance Team Support"},
                            {"text": {"type": "plain_text", "text": "Admin"}, "value": "Admin"},
                            {"text": {"type": "plain_text", "text": "IT"}, "value": "IT"},
                            {"text": {"type": "plain_text", "text": "Resource Allocation"}, "value": "Resource Allocation"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "type_block",
                    "label": {"type": "plain_text", "text": "Issue Type"},
                    "element": {
                        "type": "static_select",
                        "action_id": "type_input",
                        "options": [
                        {
                            "text": { "type": "plain_text", "text": "Bug" },
                            "value": "Bug"
                        },] 
                    }
                },
                {
                    "type": "input",
                    "block_id": "desc_block",
                    "label": {"type": "plain_text", "text": "Description"},
                    "element": {"type": "plain_text_input", "action_id": "desc_input", "multiline": True}
                }
            ]
        }

        payload = {"trigger_id": trigger_id, "view": modal_view}
        r = requests.post("https://slack.com/api/views.open", headers=headers, data=json.dumps(payload))
        frappe.log_error("Slack Modal Response", r.json())

    except Exception as e:
        frappe.log_error("Open Modal Error", frappe.get_traceback())

@frappe.whitelist(allow_guest=True)
def fetch_issue_types(category):
    try:
        issue_types = frappe.get_all(
            "Issue Type",
            filters={"custom_issue_category": category},
            fields=["name"]
        )

        options = [
            {"text": {"type": "plain_text", "text": it["name"]}, "value": it["name"]}
            for it in issue_types
        ]

        return {"options": options}

    except Exception:
        frappe.log_error("Fetch Issue Types Error", frappe.get_traceback())
        return {"options": []}
    
@frappe.whitelist(allow_guest=True)
def handle_interaction():
    payload = json.loads(frappe.form_dict.get("payload"))
    action = payload.get("actions", [])[0]
    selected_category = action.get("selected_option", {}).get("value")

    if action.get("action_id") == "category_input":
        # Fetch issue types for selected category
        issue_types = fetch_issue_types(selected_category)

        # Update the modal with new options
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-type": "application/json"
        }

        view_id = payload["view"]["id"]
        payload_update = {
            "view_id": view_id,
            "hash": payload["view"]["hash"],
            "view": payload["view"]
        }

        # inject new issue type options
        for block in payload_update["view"]["blocks"]:
            if block["block_id"] == "type_block":
                block["element"]["options"] = issue_types["options"]

        requests.post("https://slack.com/api/views.update", headers=headers, data=json.dumps(payload_update))


# 3. Handle Modal Submit → Create ERPNext Issue
@frappe.whitelist(allow_guest=True)
def handle_modal_submission(payload):
    """Triggered when user submits modal"""
    try:
        data = json.loads(payload)
        values = data["view"]["state"]["values"]
        user_id = data.get("user_id") 
        slack_user_email = get_email_id_from_slack_user_id(user_id)
        emp=frappe.get_doc('Employee',{'user_id':slack_user_email})

        subject = values["subject_block"]["subject_input"]["value"]
        priority = values["priority_block"]["priority_input"]["selected_option"]["value"]
        category = values["category_block"]["category_input"]["selected_option"]["value"]
        issue_type = values["type_block"]["type_input"]["selected_option"]["value"]
        description = values["desc_block"]["desc_input"]["value"]

        # Create Issue in ERPNext
        issue = frappe.get_doc({
            "doctype": "Issue",
            "subject": subject,
            "priority": priority,
            "custom_issue_category": category,
            "issue_type": issue_type,
            "description": description,
            "custom_employee":emp.get('name')
        })
        issue.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"ok": True, "message": f"Issue {issue.name} created successfully!"}

    except Exception as e:
        frappe.log_error("Modal Submission Error", frappe.get_traceback())
        return {"ok": False, "error": str(e)}