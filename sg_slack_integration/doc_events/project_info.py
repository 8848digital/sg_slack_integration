
import frappe
import requests
import re

import json
from frappe.utils.response import build_response

from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id


@frappe.whitelist(allow_guest=True)
def get_info():
	try:
		req = frappe.request
		frappe.log_error("UAT payload", req)
		frappe.log_error("UAT Payload 2", req.form)
		text = req.form.get("text")  # slash command input
		user_id = req.form.get("user_id")  # Slack user ID
		response_url = req.form.get("response_url")

		if not text:
			msg_block = [
				{"type": "mrkdwn",
					"text": f"❌ Please provide valid parameters: `/get-info [project-id] [members|project_details]`"}
			]
			return slack_response(response_url, msg_block)

		parts = text.split()
		if len(parts) != 2:
			msg_block = [
				{"type": "mrkdwn",
					"text": "❌ Usage: `/get-info [project-id] [members|proj_details]`"}
			]
			return slack_response(response_url, msg_block)

		project_id, info_type = parts

		# Lookup Slack user_id -> ERPNext email
		slack_user_email = get_email_id_from_slack_user_id(user_id)
		if not slack_user_email:
			msg_block = [
				{"type": "mrkdwn", "text": f"⚠️ Could not identify you in ERP system."}]
			return slack_response(response_url, msg_block)

		# Check if user has 'Partner' role
		user_roles = frappe.get_roles(slack_user_email)
		if "Partner" not in user_roles:
			msg_block = [
				{"type": "mrkdwn", "text": f"🚫 You do not have permission to access project details. Partner role required."}
			]
			return slack_response(response_url, msg_block)

		# Validate project_id
		project_id = str(project_id).strip()
		match = re.match(r'^(?:([A-Za-z]+)-)?(\d{4,})$', project_id)
		if not match:
			msg_block = [
				{"type": "mrkdwn",
					"text": "🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits)."}
			]
			return slack_response(response_url, msg_block)

		prefix, digits = match.groups()
		if prefix and prefix.lower() != "proj":
			msg_block = [
				{"type": "mrkdwn",
					"text": "🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`)."}
			]
			return slack_response(response_url, msg_block)

		# Normalize project_id
		project_id = f"PROJ-{digits}"
		frappe.log_error("74", project_id)
		# Fetch the project
		project_doc = ""
		if frappe.db.exists("Project", project_id):
			frappe.log_error("78, project exists")
			project_doc = frappe.get_doc("Project", project_id)
		else:
			msg_block = [
				{"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}]
			return slack_response(response_url, msg_block)

		if info_type == "members":
			frappe.log_error("86")
			members = []
			msg_block = []
			ped_doc = ""
			if ped_exists := frappe.db.exists("Project Employee Distribution", {"project": project_id}):
				ped_doc = frappe.get_doc("Project Employee Distribution", ped_exists)
				members = frappe.get_all("Project Employee Distribution Detail", filters={
                                    "parent": ped_exists, "parenttype": "Project Employee Distribution"}, fields=["employee_name", "designation", "from_date", "to_date"])
				frappe.log_error("94", str(members))
			else:
				msg_block = [
					{"type": "mrkdwn", "text": f"ℹ️ No members found for project `{project_id}`."}
				]
				return slack_response(response_url, msg_block)
			msg_block = [
				{"type": "mrkdwn", "text": f"These are the members found for project `{project_id}`."}
			]
			msg_block.append(
				{"type": "mrkdwn", "text": f"Partner: {ped_doc.project_lead_name}"})
			msg_block.append(
				{"type": "mrkdwn", "text": f"Engagement Manager: {ped_doc.project_manager_name}"})
			for m in members:
				msg_block.append(
					{"type": "mrkdwn", "text": f"• {m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')}"})
			return slack_response(response_url, msg_block)

		elif info_type == "proj_details":
			frappe.log_error("110")
			msg_block = [
				{"type": "mrkdwn", "text": f"*Project ID:*\n{project_doc.name}"},
				{"type": "mrkdwn", "text": f"*Project Name:*\n{project_doc.project_name}"},
				{"type": "mrkdwn", "text": f"*Workflow State:*\n{project_doc.worklfow_state}"},
				{"type": "mrkdwn", "text": f"*Status:*\n{project_doc.status}"},
				{"type": "mrkdwn", "text": f"*Project Type:*\n{project_doc.project_type}"},
				{"type": "mrkdwn", "text": f"*Service Line:*\n{project_doc.service_line}"},
				{"type": "mrkdwn", "text": f"*Expected Start:*\n{project_doc.expected_start_date}"},
				{"type": "mrkdwn", "text": f"*Expected End:*\n{project_doc.expected_end_date}"},
				{"type": "mrkdwn", "text": f"*Sharepoint Link:*\n{project_doc.custom_sharepoint_link}"},
				{"type": "mrkdwn", "text": f"*Sharepoint Folder Name:*\n{project_doc.custom_folder_name}"},
				{"type": "mrkdwn", "text": f"*Customer:*\n{project_doc.customer}"},
				{"type": "mrkdwn", "text": f"*Customer Name:*\n{project_doc.custom_folder_name}"},
				{"type": "mrkdwn", "text": f"*Partner:*\n{project_doc.project_lead_name}"},
				{"type": "mrkdwn", "text": f"*Engagement Manager:*\n{project_doc.project_manager_name}"}
			]
			return slack_response(response_url, msg_block)

		else:
			msg_block = [
				{"type": "mrkdwn", "text": "❌ Invalid info type. Use `members` or `project_details`."}
			]
			return slack_response(response_url, msg_block)
	except Exception as e:
		frappe.log_error("error", e)


@frappe.whitelist(allow_guest=True)
def manage_group():

	req = frappe.request
	frappe.log_error("Group Manage Payload", req)
	frappe.log_error("Group Manage Payload Form", req.form)
	text = req.form.get("text")  # slash command input
	user_id = req.form.get("user_id")  # Slack user ID
	response_url = req.form.get("response_url")  # Slack response URL

	if not text:
		msg_block = [
			{"type": "mrkdwn",
				"text": "❌ Please provide valid parameters: `/group-manage [project-id] [view|add|remove] [emp-id]`"}
		]
		return slack_response(response_url, msg_block)

	parts = text.split()
	if len(parts) < 2 or len(parts) > 3:
		msg_block = [
			{"type": "mrkdwn",
				"text": "❌ Usage: `/group-manage [project-id] [view|add|remove] [emp-id]`"}
		]
		return slack_response(response_url, msg_block)

	project_id = parts[0]
	action = parts[1].lower()
	emp_id = parts[2] if len(parts) == 3 else None

	# Validate action
	if action not in ["view", "add", "remove"]:
		msg_block = [
			{"type": "mrkdwn", "text": "❌ Invalid action. Use `view`, `add`, or `remove`."}
		]
		return slack_response(response_url, msg_block)

	# Validate project_id
	project_id = str(project_id).strip()
	match = re.match(r'^(?:([A-Za-z]+)-)?(\d{4,})$', project_id)
	if not match:
		msg_block = [
			{"type": "mrkdwn",
				"text": "🚫 Invalid Project ID. Use formats like `PROJ-1234` (letters, hyphen, 4+ digits) or `1234` (4+ digits)."}
		]
		return slack_response(response_url, msg_block)

	prefix, digits = match.groups()
	if prefix and prefix.lower() != "proj":
		msg_block = [
			{"type": "mrkdwn",
				"text": "🚫 Invalid prefix. Project ID must start with `PROJ` (e.g., `PROJ-1234`)."}
		]
		return slack_response(response_url, msg_block)

	project_id = f"PROJ-{digits}"

	# Validate emp_id for add/remove actions
	if action in ["add", "remove"] and not emp_id:
		msg_block = [
			{"type": "mrkdwn", "text": "❌ Employee ID required for `add` or `remove` actions."}
		]
		return slack_response(response_url, msg_block)

	if emp_id:
		emp_id = str(emp_id).strip()
		if not re.match(r'^SG(?:-[EQL])?-\d{3,}$', emp_id):
			msg_block = [
				{"type": "mrkdwn",
					"text": "🚫 Invalid Employee ID. Use formats like `SG-123`, `SG-E-123`, `SG-Q-123`, or `SG-L-123` (SG, optional E/Q/L, hyphen, 3+ digits)."}
			]
			return slack_response(response_url, msg_block)

	# Lookup Slack user_id -> ERPNext email
	slack_user_email = get_email_id_from_slack_user_id(user_id)
	if not slack_user_email:
		msg_block = [
			{"type": "mrkdwn", "text": "⚠️ Could not identify you in ERP system."}
		]
		return slack_response(response_url, msg_block)

    # Check if user has 'Project Manager' role
	user_roles = frappe.get_roles(slack_user_email)
	if "Projects Manager" not in user_roles:
		msg_block = [
			{"type": "mrkdwn", "text": "🚫 You do not have permission to manage project groups. Project Manager role required."}
		]
		return slack_response(response_url, msg_block)

	# Fetch the project
	if not frappe.db.exists("Project", project_id):
		msg_block = [
			{"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}
		]
		return slack_response(response_url, msg_block)

	project_doc = frappe.get_doc("Project", project_id)
	ped_exists = ""
	ped_doc = ""
	if ped_exists := frappe.db.exists("Project Employee Distribution", {"project": project_id}):
		ped_doc = frappe.get_doc("Project Employee Distribution", ped_exists)
	else:
		msg_block = [
			{"type": "mrkdwn", "text": f"ℹ️ No members found for project `{project_id}`."}
		]
		return slack_response(response_url, msg_block)

	if action == "view":
		members = []
		msg_block = []
		members = frappe.get_all("Project Employee Distribution Detail", filters={"parent": ped_exists, "parenttype": "Project Employee Distribution"}, fields=[
		                         "employee", "employee_name", "designation", "from_date", "to_date"])
		msg_block = [
			{"type": "mrkdwn", "text": f"Members of project `{project_id}`:"}
		]
		for m in members:
			msg_block.append(
				{"type": "mrkdwn",
					"text": f"• {m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')} (ID: {m.get('employee')})"}
			)
		return slack_response(response_url, msg_block)

	elif action == "add":
		pass
        # Check if employee exists
        # if not frappe.db.exists("Employee", emp_id):
        #     msg_block = [
        #         {"type": "mrkdwn", "text": f"🚫 No employee found with ID `{emp_id}`."}
        #     ]
        #     return slack_response(response_url, msg_block)

        # # Check if employee is already assigned
        # if frappe.db.exists("Project Employee Distribution Detail", {"parent": project_id, "employee": emp_id}):
        #     msg_block = [
        #         {"type": "mrkdwn", "text": f"⚠️ Employee `{emp_id}` is already assigned to project `{project_id}`."}
        #     ]
        #     return slack_response(response_url, msg_block)

        # # Add employee to project
        # employee_doc = frappe.get_doc("Employee", emp_id)
        # project_doc.append("employees", {
        #     "employee": emp_id,
        #     "employee_name": employee_doc.employee_name,
        #     "designation": employee_doc.designation or "N/A",
        #     "from_date": frappe.utils.nowdate(),
        #     "to_date": project_doc.expected_end_date or frappe.utils.add_days(frappe.utils.nowdate(), 30)
        # })
        # project_doc.save()
        # frappe.db.commit()

        # msg_block = [
        #     {"type": "mrkdwn", "text": f"✅ Employee `{emp_id}` ({employee_doc.employee_name}) added to project `{project_id}`."}
        # ]
        # return slack_response(response_url, msg_block)

	elif action == "remove":
		# Check if employee is assigned
		if not frappe.db.exists("Project Employee Distribution Detail", {"parent": ped_exists, "employee": emp_id}):
			msg_block = [
				{"type": "mrkdwn", "text": f"⚠️ Employee `{emp_id}` is not assigned to project `{project_id}`."}
			]
			return slack_response(response_url, msg_block)

		# Remove employee from project
		frappe.db.delete("Project Employee Distribution Detail", {
			"parent": ped_exists,
			"employee": emp_id
		})
		frappe.db.commit()

		msg_block = [
			{"type": "mrkdwn", "text": f"✅ Employee `{emp_id}` removed from project `{project_id}`."}
		]
		return slack_response(response_url, msg_block)


def slack_response(response_url, message_block):
	response = {
		"response_type": "ephemeral",
		"blocks": [
			{
				"type": "section",
				"fields": message_block
			}
		]
	}
	result = requests.post(response_url, json=response)
	frappe.log_error("result", result.text)
	# Return a 200 OK response with an empty body
	frappe.local.response["http_status_code"] = 200

	return
