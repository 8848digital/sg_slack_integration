import frappe
import requests
import json
from frappe.utils.file_manager import save_file

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
    
def open_modal(trigger_id, user_id, channel_id):
    try:
        issue_types=frappe.get_all('Issue Type',{'custom_issue_category':['is','set'],'custom_disable':0},['name','custom_issue_category'])
        category_options = [
        {
            "text": {"type": "plain_text", "text": f"{d['custom_issue_category']}_{d['name']}"},
            "value": f"{d['custom_issue_category']}_{d['name']}"
        }
            for d in issue_types if d.get("custom_issue_category")
        ]
        SLACK_BOT_TOKEN = frappe.db.get_single_value("Slack Integration Settings", "issue_token")  # store securely


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
                        "placeholder": {"type": "plain_text", "text": "Select Category"},
                        "options": category_options
                    }
                },
                {
                    "type": "input",
                    "block_id": "desc_block",
                    "label": {"type": "plain_text", "text": "Description"},
                    "element": {"type": "plain_text_input", "action_id": "desc_input", "multiline": True}
                },
                {
                    "type": "input",
                    "block_id": "input_block_id",
                    "label": {
                    "type": "plain_text",
                    "text": "Upload Files"},
                    "element": {
                    "type": "file_input",
                    "action_id": "file_input_action_id_1",
                    "filetypes": ["jpg", "png"],
                    "max_files": 5,
                    },
                }
            ]
        }

        payload = {"trigger_id": trigger_id, "view": modal_view}
        r = requests.post("https://slack.com/api/views.open", headers=headers, data=json.dumps(payload))
        frappe.log_error("Slack Modal Response", r.json())

    except Exception as e:
        print(e)
        frappe.log_error("Open Modal Error", frappe.get_traceback())


@frappe.whitelist(allow_guest=True)
def fetch_issue_types():
    """This endpoint will be called when user selects Category"""
    try:
        payload = frappe.form_dict.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        frappe.log_error('Payload-handle',payload)

        actions = payload.get("actions", [])
        view = payload.get("view", {})
        view_id = view.get("id")

        if not actions:
            return

        # Get selected category
        category = actions[0]["selected_option"]["value"]

        # Fetch issue types from ERPNext
        issue_types = frappe.get_all(
            "Issue Type",
            filters={"custom_issue_category": category},
            fields=["name"]
        )

        options = [
            {"text": {"type": "plain_text", "text": it["name"]}, "value": it["name"]}
            for it in issue_types
        ]

        import copy
        updated_view = copy.deepcopy(view)
        for b in updated_view["blocks"]:
            if b["block_id"] == "type_block":
                b["element"] = {
                    "type": "static_select",
                    "action_id": "type_selected",
                    "placeholder": {"type": "plain_text", "text": "Select Issue Type"},
                    "options": options
                }
        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-type": "application/json"
        }
        data = {
            "view_id": view_id,
            "hash": view.get("hash"),   # include hash
            "view": updated_view
        }
        r = requests.post("https://slack.com/api/views.update", headers=headers, data=json.dumps(data))
        frappe.log_error("Slack Views Update Response", r.json())

    except Exception:
        frappe.log_error("Block Actions Error", frappe.get_traceback())

@frappe.whitelist(allow_guest=True)
def handle_modal_submission(payload):
    """Triggered when user submits modal"""
    try:
        data = json.loads(payload)
        frappe.log_error('Data Submit', data)
        values = data["view"]["state"]["values"]
        user_id = data.get('user', {}).get('id')
        SLACK_BOT_TOKEN = frappe.db.get_single_value("Slack Integration Settings", "issue_token")  # store securely
        slack_user_email = get_email_id_from_slack_user_id(user_id,SLACK_BOT_TOKEN)

        # respond to Slack first → so modal closes properly
        frappe.local.response["http_status_code"] = 200
        # frappe.local.response["type"] = "json"
        # frappe.local.response["response_type"] = "clear"
        # frappe.local.response["message"] = {"response_action": "clear"}

        # enqueue ERPNext issue creation in background
        frappe.enqueue(create_issue_from_slack_submission, data=data, slack_user_email=slack_user_email,user_id=user_id,SLACK_BOT_TOKEN=SLACK_BOT_TOKEN)
        return 
    except Exception as e:
        frappe.log_error("Modal Submission Error", frappe.get_traceback())
        return {
            "response_action": "errors",
            "errors": {"desc_block": "Something went wrong. Please try again."}
        }


def create_issue_from_slack_submission(data, slack_user_email,user_id,SLACK_BOT_TOKEN):
    """Actually create ERPNext Issue in background"""
    try:
        values = data["view"]["state"]["values"]
        emp = None
        if frappe.db.exists('Employee', {'user_id': slack_user_email}):
            emp = frappe.get_doc('Employee', {'user_id': slack_user_email})

        if values["category_block"]["category_input"]["selected_option"]["value"]:
            combine_option = values["category_block"]["category_input"]["selected_option"]["value"]
            category = combine_option.split('_')[0]
            issue_type = combine_option.split('_')[-1]
        else:
            category, issue_type = None, None

        subject = values["subject_block"]["subject_input"]["value"]
        priority = values["priority_block"]["priority_input"]["selected_option"]["value"]
        description = values["desc_block"]["desc_input"]["value"]

        frappe.set_user(slack_user_email)

        issue = frappe.get_doc({
            "doctype": "Issue",
            "subject": subject,
            "priority": priority,
            "custom_issue_category": category,
            "issue_type": issue_type,
            "description": description,
            "custom_employee": emp.name if emp else None
        })
        issue.insert(ignore_permissions=True)
        frappe.db.commit()
        files = []
        file_action = values.get("input_block_id", {}).get("file_input_action_id_1")
        if file_action and "files" in file_action:
            files = file_action["files"]
        if files:
            attach_slack_files_to_issue(issue, files,SLACK_BOT_TOKEN)
        post_message_with_id(issue.name,user_id,emp,SLACK_BOT_TOKEN)

    except Exception:
        frappe.log_error("Issue Creation Error", frappe.get_traceback())

def post_message_with_id(issue,user_id,emp,SLACK_BOT_TOKEN):
    slack_token = SLACK_BOT_TOKEN
    if slack_token and len(slack_token) > 0:
        link=frappe.utils.get_url_to_form('Issue',issue)
        block_data=[]
        header_block = {
                "type": "header",
                "text": {"type": "plain_text", "text": 'Issue created- ' + issue}
            }
        block_data.append(header_block)
        content = f'Dear {emp.get("employee_name")}, your issue have been successfully created on Erpnext'
        sections = [
                {"title":f'{content}','content':link},
            ]
        for section in sections:
                description_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text":  f"*{section['title']}*: {section['content']}"
                    },
                }
                block_data.append(description_block)
        if user_id:
            payload = {
                "text": "Issue Created",
                "blocks": block_data
            }
            payload["channel"] = user_id
            payload = payload.copy()
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {slack_token}",
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, json=payload)

def get_email_id_from_slack_user_id(slack_user_id,SLACK_BOT_TOKEN):
    """
    Uses Slack API to retrieve user email based on Slack user ID,
    then checks if that email exists in ERPNext users.
    """
    if not slack_user_id:
        return None

    token = SLACK_BOT_TOKEN
    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"https://slack.com/api/users.info?user={slack_user_id}"
    response = requests.get(url, headers=headers)
    data = response.json()

    if not data.get("ok"):
        frappe.log_error("Slack API Error | get_email_id_from_slack_user_id", data)
        return None

    slack_email = data.get("user", {}).get("profile", {}).get("email")

    if not slack_email:
        return None

    # Validate against ERPNext users
    user_exists = frappe.db.exists("User", {"email": slack_email})
    return slack_email if user_exists else None

def attach_slack_files_to_issue(issue, files,slack_token):
    """Download Slack uploaded files and attach to Issue"""
    headers = {"Authorization": f"Bearer {slack_token}"}

    for f in files:
        file_url = f.get("url_private_download")
        file_name = f.get("name")

        # Download from Slack
        resp = requests.get(file_url, headers=headers)
        if resp.status_code != 200:
            frappe.log_error(f"Failed to download {file_name} from Slack", "Slack File Download Error")
            continue

        # Save in ERPNext
        saved_file = save_file(
            fname=file_name,
            content=resp.content,
            dt="Issue",
            dn=issue.name,
            folder="Home/Attachments",
            is_private=1
        )
