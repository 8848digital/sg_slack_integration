import frappe
import requests
import re
import json
import traceback
from frappe.utils.response import build_response

from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id
from sg_slack_integration.doc_events.utils import create_slack_log_for_commands

@frappe.whitelist(allow_guest=True)
def get_info():
    try:
        req = frappe.request
        frappe.log_error("Get Info Payload", f"Request: {req}")
        frappe.log_error("Get Info Payload Form", f"Form: {req.form}")
        text = req.form.get("text")  # slash command input
        user_id = req.form.get("user_id")  # Slack user ID
        response_url = req.form.get("response_url")

        if not text:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Please provide valid parameters: `/get-info [project-id] [members|proj_details]`"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Please provide valid parameters: `/get-info [project-id] [members|proj_details]`")

        parts = text.split()
        if len(parts) != 2:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Usage: `/get-info [project-id] [members|proj_details]`"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Usage: `/get-info [project-id] [members|proj_details]`")

        project_id, info_type = parts
        info_type = info_type.lower().strip()  # Normalize info_type

        # Lookup Slack user_id -> ERPNext email
        slack_user_email = get_email_id_from_slack_user_id(user_id)
        if not slack_user_email:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "⚠️ Could not identify you in ERP system."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="⚠️ Could not identify you in ERP system.")

        # Check if user has 'Partner' role
        user_roles = frappe.get_roles(slack_user_email)
        if "Partner" not in user_roles:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 You do not have permission to access project details. Partner role required."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="🚫 You do not have permission to access project details. Partner role required.")
        frappe.set_user("Administrator")
        # Validate project_id
        project_id = str(project_id).strip()
        match = re.match(r'^(?:([A-Za-z]+)-)?(\d{4,})$', project_id)
        if not match:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits)."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits).")

        prefix, digits = match.groups()
        if prefix and prefix.lower() != "proj":
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`)."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`).")

        # Normalize project_id
        project_id = f"PROJ-{digits}"
        frappe.log_error("Normalized Project ID", project_id)

        # Fetch the project
        if not frappe.db.exists("Project", project_id):
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response=f"🚫 No project found with ID `{project_id}`.")

        project_doc = frappe.get_doc("Project", project_id)
        frappe.log_error("Project Fetched", f"Project ID: {project_id}")

        if info_type == "members":
            ped_docs = frappe.get_all("Project Employee Distribution", filters={"project": project_id}, fields=[
                                      "name", "project_lead_name", "project_manager_name"], limit=1)
            if not ped_docs:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"ℹ No members found for project `{project_id}`."}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response=f"ℹ No members found for project `{project_id}`.")

            ped_doc = ped_docs[0]
            members = frappe.get_all("Project Employee Distribution Detail", filters={
                "parent": ped_doc.name,
                "parenttype": "Project Employee Distribution"
            }, fields=["employee_name", "designation", "from_date", "to_date"])
            frappe.log_error("Members Fetched", f"Members: {members}")

            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*These are the members found for project `{project_id}`*"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Partner:* {ped_doc.get('project_lead_name') or 'N/A'}\n*Engagement Manager:* {ped_doc.get('project_manager_name') or 'N/A'}"
                    }
                }
            ]

            if members:
                member_lines = "\n".join(
                    f"• {m.get('employee_name') or 'N/A'} ({m.get('designation') or 'N/A'}) - {m.get('from_date') or 'N/A'}-{m.get('to_date') or 'N/A'}"
                    for m in members
                )
                msg_block.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Members:*\n{member_lines}"}
                })
            else:
                msg_block.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "No team members assigned."}
                })

            frappe.log_error("Message Block (members)",
                             json.dumps(msg_block, indent=2))
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response=json.dumps(msg_block, indent=2))

        elif info_type == "proj_details":
            # Group fields into logical sections to avoid exceeding 3000 characters
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Project Details for `{project_id}`*"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Project ID:* {project_doc.get('name') or 'N/A'}\n"
                                f"*Project Name:* {project_doc.get('project_name') or 'N/A'}\n"
                                f"*Workflow State:* {project_doc.get('workflow_state') or 'N/A'}\n"
                                f"*Status:* {project_doc.get('status') or 'N/A'}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Project Type:* {project_doc.get('project_type') or 'N/A'}\n"
                                f"*Service Line:* {project_doc.get('service_line') or 'N/A'}\n"
                                f"*Expected Start Date:* {project_doc.get('expected_start_date') or 'N/A'}\n"
                                f"*Expected End Date:* {project_doc.get('expected_end_date') or 'N/A'}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Sharepoint Link:* {project_doc.get('custom_sharepoint_link') or 'N/A'}\n"
                                f"*Sharepoint Folder Name:* {project_doc.get('custom_folder_name') or 'N/A'}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Customer:* {project_doc.get('customer') or 'N/A'}\n"
                                f"*Customer Name:* {project_doc.get('customer_name') or project_doc.get('customer') or 'N/A'}\n"
                                f"*Partner:* {project_doc.get('project_lead_name') or 'N/A'}\n"
                                f"*Engagement Manager:* {project_doc.get('project_manager_name') or 'N/A'}"
                    }
                }
            ]

            # Handle individual fields that might exceed 3000 characters (e.g., a very long Sharepoint link)
            final_blocks = []
            for block in msg_block:
                text = block["text"]["text"]
                if len(text) <= 3000:
                    final_blocks.append(block)
                    continue

                # Split the text into chunks under 3000 characters
                lines = text.split("\n")
                chunk = []
                current_text = ""
                for line in lines:
                    if len(current_text) + len(line) + 1 <= 3000:  # +1 for newline
                        current_text += line + "\n"
                    else:
                        if current_text:
                            final_blocks.append({
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": current_text.rstrip()}
                            })
                        current_text = line + "\n"

                if current_text:
                    final_blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": current_text.rstrip()}
                    })

            frappe.log_error("Message Block (proj_details)",
                             json.dumps(final_blocks, indent=2))
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response=json.dumps(final_blocks, indent=2))

        else:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Invalid info type. Use `members` or `proj_details`."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Invalid info type. Use `members` or `proj_details`.")

    except Exception as e:
        frappe.log_error(
            "Get Info Error", f"Error: {str(e)}\nTraceback: {traceback.format_exc()}")
        msg_block = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "❌ An error occurred while processing your request. Please try again later."}
            }
        ]
        return slack_response(response_url, msg_block, user_id, "Error", req.form.get('command'), text, response="❌ An error occurred while processing your request. Please try again later.", error=frappe.get_traceback(e))



@frappe.whitelist(allow_guest=True)
def manage_group():
    try:
        req = frappe.request
        frappe.log_error("Group Manage Payload", f"Request: {req}")
        frappe.log_error("Group Manage Payload Form", f"Form: {req.form}")
        text = req.form.get("text")  # Slash command input
        user_id = req.form.get("user_id")  # Slack user ID
        response_url = req.form.get("response_url")  # Slack response URL

        # Validate input immediately
        if not text:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Please provide valid parameters: `/group-manage [project-id] [view|create|add|remove] [email-group-name]/[user-id]`"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Please provide valid parameters: `/group-manage [project-id] [view|create|add|remove] [email-group-name]/[user-id]`")

        parts = text.split()
        if len(parts) < 2 or len(parts) > 3:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Usage: `/group-manage [project-id] [view|create|add|remove] [email-group-name]/[user-id]`"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Usage: `/group-manage [project-id] [view|create|add|remove] [email-group-name]/[user-id]`")

        # Respond to Slack immediately
        msg_block = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "⏳ Processing your request... You'll receive a response shortly."}
            }
        ]
        # Send immediate response to Slack
        slack_response(response_url, msg_block)

        # Enqueue the actual processing in the background
        frappe.enqueue(
            process_manage_group,
            queue="long",
            timeout=3600,
            is_async=True,
            job_name="manage_group_background",
            text=text,
            user_id=user_id,
            command=req.form.get('command'),
            response_url=response_url
        )

        # Return an empty 200 OK response to Frappe (since we've already responded to Slack)
        frappe.local.response["http_status_code"] = 200
        # frappe.local.response["content_type"] = "application/json"
        # frappe.local.response["data"] = ""
        return

    except Exception as e:
        frappe.log_error("Manage Group Immediate Response Error",
                         f"Error: {str(e)}\nTraceback: {traceback.format_exc()}")
        msg_block = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "❌ An error occurred while initiating your request. Please try again later."}
            }
        ]
        return slack_response(response_url, msg_block, user_id, "Error", req.form.get('command'), text, response="❌ An error occurred while initiating your request. Please try again later.", error=frappe.get_traceback(e))


def process_manage_group(text, user_id, response_url, command):
    """
    Background job to process the manage_group logic and send the final response to Slack.
    """
    try:
        msg_block = []
        # Lookup Slack user_id -> ERPNext email
        slack_user_email = get_email_id_from_slack_user_id(user_id)
        if not slack_user_email:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "⚠️ Could not identify you in ERP system."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="⚠️ Could not identify you in ERP system.")

        # Validate email format
        # email_pattern = r'^[a-zA-Z0-9._%+-]+@strategicgears\.com$'
        # if not re.match(email_pattern, slack_user_email, re.IGNORECASE):
        #     msg_block = [
        #         {
        #             "type": "section",
        #             "text": {"type": "mrkdwn", "text": "⚠️ Invalid email format. Email must be in the format `user@strategicgears.com`."}
        #         }
        #     ]
        #     return slack_response(response_url, msg_block)

        # Check if user has 'Projects Manager' role
        user_roles = frappe.get_roles(slack_user_email)
        if "Projects Manager" not in user_roles:  # Fixed role name to match error message
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 You do not have permission to manage project groups. Projects Manager role required."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="🚫 You do not have permission to manage project groups. Projects Manager role required.")

        parts = text.split()
        project_id = parts[0]
        action = parts[1].lower()
        param3 = parts[2] if len(parts) == 3 else None

        # Validate action
        if action not in ["view", "create", "add", "remove"]:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Invalid action. Use `view`, `create`, `add`, or `remove`."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="❌ Invalid action. Use `view`, `create`, `add`, or `remove`.")

        # Validate project_id
        project_id = str(project_id).strip()
        match = re.match(r'^(?:([A-Za-z]+)-)?(\d{4,})$', project_id)
        if not match:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits)."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits).")

        prefix, digits = match.groups()
        if prefix and prefix.lower() != "proj":
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`)."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`).")

        project_id = f"PROJ-{digits}"
        frappe.log_error("Normalized Project ID", project_id)

        # Fetch the project
        if not frappe.db.exists("Project", project_id):
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"🚫 No project found with ID `{project_id}`.")

        project_doc = frappe.get_doc("Project", project_id)
        owners = [
            project_doc.custom_project_lead_email,
            project_doc.custom_project_manager_email,
            project_doc.custom_project_leader_email
        ]
        owners = list(filter(None, set(owners)))  # Remove None and duplicates
        eg_created = project_doc.custom_email_group if project_doc.custom_email_group else False
        frappe.log_error("Project Fetched", f"Project ID: {project_id}")

        frappe.set_user("Administrator")

        if action == "view":
            members = []
            if not eg_created:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"ℹ No Email Group found for project `{project_id}`."}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"ℹ No Email Group found for project `{project_id}`.")

            email_group = frappe.get_all("Email Group", filters={
                                         "custom_project": project_id}, limit=1)
            if email_group:
                email_group = email_group[0].get('name')
                members = frappe.get_all("Email Group Member", filters={
                                         "email_group": email_group}, fields=["name", "email"])

            frappe.log_error("Members Fetched", f"Members: {members}")

            if members:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Members of Group - {eg_created} for Project `{project_id}`*"}
                    }
                ]
                member_lines = "\n".join(
                    f"• *{m.get('email')}*"
                    for m in members
                )
                msg_block.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Members:*\n{member_lines}"}
                })
            else:
                msg_block.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "No team members added."}
                })
            frappe.log_error("Message Block (view)",
                             json.dumps(msg_block, indent=2))
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=json.dumps(msg_block, indent=2))

        if action == "create":
            if eg_created:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"❌ This Project is already linked to Email Group - {eg_created}"}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"❌ This Project is already linked to Email Group - {eg_created}")

            if not param3:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "❌ Email Group Name Required for `create` action."}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", command, text, response="❌ Email Group Name Required for `create` action.")

            param3 = str(param3).strip()
            if frappe.db.exists("Email Group", param3):
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "❌ This Name is taken, please try again with a different Name"}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", command, text, response="❌ This Email group Name is taken, please try again with a different Name")

            frappe.set_user(slack_user_email)
            eg_creation_successful = create_email_group(param3, project_id)
            frappe.set_user("Administrator")
            if not eg_creation_successful:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "❌ There was an error creating Email Group"}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", command, text, response="❌ There was an error creating Email Group")

            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"✅ Email Group - {param3} created successfully and linked with Project"}
                }
            ]
            frappe.enqueue(
                add_owners_to_email_group,
                queue="long",
                timeout=3600,
                is_async=True,
                job_name="add_owners_to_email_group_project",
                owners=owners,
                email_group=param3
            )
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"✅ Email Group - {param3} created successfully and linked with Project")

        # Validate emails for add/remove actions
        if action in ["add", "remove"] and not param3:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Usage: `/group-manage [project-id] [add|remove] [user-id]`"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response="❌ Usage: `/group-manage [project-id] [add|remove] [user-id]`")

        if not eg_created:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"❌ No Email Group linked to project `{project_id}`. Please create one first using `create` action."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"❌ No Email Group linked to project `{project_id}`. Please create one first using `create` action.")

        # Validate and normalize email addresses
        # email_pattern = r'^[a-zA-Z0-9._%+-]+@strategicgears\.com$'
        param3 = str(param3).strip()
        emails = [email.strip() for email in param3.split(",")]
        # invalid_emails = []
        # normalized_emails = []
        # for email in emails:
        #     if not re.match(email_pattern, email, re.IGNORECASE):
        #         invalid_emails.append(email)
        #     else:
        #         # Normalize to lowercase
        #         normalized_emails.append(email.lower())

        # if invalid_emails:
        #     msg_block = [
        #         {
        #             "type": "section",
        #             "text": {"type": "mrkdwn", "text": f"🚫 Invalid email(s): {', '.join(invalid_emails)}. Emails must be in the format `user@strategicgears.com`."}
        #         }
        #     ]
        #     return slack_response(response_url, msg_block)

        # Check if users exist and are enabled
        non_existent_emails = []
        for email in emails:
            email = f"{email}@strategicgears.com"
            if not frappe.db.exists("User", {"email": email, "enabled": 1}):
                non_existent_emails.append(email)

        if non_existent_emails:
            msg_block = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🚫 User(s) not found or disabled: {', '.join(non_existent_emails)}."}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=f"🚫 User(s) not found or disabled: {', '.join(non_existent_emails)}.")

        if action == "add":
            error = []
            added_emails = []
            for email in emails:
                email = f"{email}@strategicgears.com"
                # Check if user is already in the email group
                if frappe.db.exists("Email Group Member", {"email_group": eg_created, "email": email}):
                    error.append(f"{email} is already in the email group")
                    continue

                try:
                    frappe.set_user(slack_user_email)
                    egm = frappe.new_doc("Email Group Member")
                    egm.email_group = eg_created
                    egm.email = email
                    egm.custom_project = project_id
                    egm.save(ignore_permissions=True)
                    frappe.set_user("Administrator")
                    added_emails.append(email)
                except Exception as e:
                    error.append(f"Error adding {email}: {str(e)}")

            if error:
                frappe.log_error("Slack Group Manager Error | ADD", str(error))
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"⚠️ Some errors occurred while adding users. Successfully added: {', '.join(added_emails) if added_emails else 'None'}. Errors: {'; '.join(error)}"}
                    }
                ]
            else:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"✅ User(s) *{', '.join(added_emails)}* added to Group - *{eg_created}* for project *{project_id}*."}
                    }
                ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=json.dumps(msg_block, indent=2))

        elif action == "remove":
            error = []
            removed_emails = []
            for email in emails:
                email = f"{email}@strategicgears.com"
                # Check if user is in the email group
                if not frappe.db.exists("Email Group Member", {"email_group": eg_created, "email": email}):
                    error.append(f"{email} is not in the email group")
                    continue

                try:
                    frappe.set_user(slack_user_email)
                    egm = frappe.get_doc("Email Group Member", {
                                         "email_group": eg_created, "email": email})
                    egm.delete(ignore_permissions=True)
                    frappe.set_user("Administrator")
                    removed_emails.append(email)
                except Exception as e:
                    error.append(f"Error removing {email}: {str(e)}")

            if error:
                frappe.log_error(
                    "Slack Group Manager Error | REMOVE", str(error))
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"⚠️ Some errors occurred while removing users. Successfully removed: {', '.join(removed_emails) if removed_emails else 'None'}. Errors: {'; '.join(error)}"}
                    }
                ]
            else:
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"✅ User(s) *{', '.join(removed_emails)}* removed from Group - *{eg_created}* for project *{project_id}*."}
                    }
                ]
            return slack_response(response_url, msg_block, user_id, "Success", command, text, response=json.dumps(msg_block, indent=2))

    except Exception as e:
        frappe.log_error("Manage Group Background Error",
                         f"Error: {str(e)}\nTraceback: {traceback.format_exc()}")
        msg_block = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "❌ An error occurred while processing your request. Please check the logs or try again later."}
            }
        ]
        return slack_response(response_url, msg_block, user_id, "Error", command, text, response="❌ An error occurred while processing your request. Please check the logs or try again later.", error=frappe.get_traceback(e))


def slack_response(response_url, message_blocks, user_id=None, status=None, cmd=None, param=None, response=None, error=None):
    create_slack_log_for_commands(
        user=user_id, status=status, cmd=cmd, param=param, response=response, error=error)

    # Validate that message_blocks is a list
    if not isinstance(message_blocks, list):
        frappe.log_error("Invalid Blocks Format",
                         f"Expected list, got: {type(message_blocks)}")
        message_blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "⚠️ Invalid message format."}
            }
        ]

    # Sanitize each block
    sanitized_blocks = []
    for block in message_blocks:
        if not isinstance(block, dict) or "type" not in block or block["type"] != "section":
            frappe.log_error("Invalid Block", f"Block: {block}")
            continue
        text_obj = block.get("text", {})
        if not isinstance(text_obj, dict) or "type" not in text_obj or "text" not in text_obj:
            frappe.log_error("Invalid Text Object", f"Text: {text_obj}")
            continue
        text = str(text_obj.get("text") or "N/A")
        if not text.strip():
            frappe.log_error("Empty Block Text", f"Text: {text}")
            continue
        sanitized_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text[:3000]  # Truncate to Slack's 3000-char limit
            }
        })

    if not sanitized_blocks:
        sanitized_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "⚠️ No valid message content available."}
        })

    # Limit to 50 blocks (Slack's limit)
    sanitized_blocks = sanitized_blocks[:50]

    # Prepare the Slack API payload
    response = {
        "response_type": "ephemeral",
        "blocks": sanitized_blocks
    }

    # Log the payload for debugging
    frappe.log_error("Slack Payload", json.dumps(response, indent=2))

    # Send the request
    headers = {"Content-Type": "application/json"}
    result = requests.post(response_url, headers=headers, json=response)

    # Log the response
    frappe.log_error("Slack Response",
                     f"Status: {result.status_code}, Body: {result.text}")

    # Return a 200 OK response with an empty body
    # frappe.local.response["http_status_code"] = 200
    # frappe.local.response["content_type"] = "application/json"
    # frappe.local.response["data"] = ""
    return


def create_email_group(eg_name, project_name):
	try:
		email_group = frappe.new_doc("Email Group")
		email_group.title = eg_name
		email_group.custom_integrate_with_erp = 1
		email_group.custom_related_to_project = 1
		email_group.custom_project = project_name
		email_group.save(ignore_permissions=True)
		frappe.db.set_value("Project", project_name,
		                    'custom_email_group', email_group.name)
		return True
	except Exception as e:
		frappe.log_error("Salck Group Manage | create_email_group",
		                 frappe.get_traceback(e))
		return False


def add_owners_to_email_group(owners, email_group):
	for each in owners:
		if each:
			member = frappe.new_doc("Email Group Member")
			member.email_group = email_group
			member.email = each
			member.save(ignore_permissions=True)
