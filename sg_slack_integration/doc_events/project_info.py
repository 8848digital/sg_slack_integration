
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
				"text": "❌ Usage: `/get-info [project-id] [members|project_details]`"}
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
			{"type": "mrkdwn", "text": f"🚫 You do not have permission to access project details."}
		]
		return slack_response(response_url, msg_block)

	# Fetch the project
	project_doc = ""
	if frappe.db.exists("Project", project_id):
		project_doc = frappe.get_doc("Project", project_id)
	else:
		msg_block = [
			{"type": "mrkdwn", "text": f"🚫 No project found with ID `{project_id}`."}]
		return slack_response(response_url, msg_block)

	if info_type == "members":
		members = frappe.get_all("Project Employee Distribution Detail", filters={
		                         "parent": project_id}, fields=["employee_name", "designation", "from_date", "to_date"])
		if not members:
			msg_block = [
				{"type": "mrkdwn", "text": f"ℹ️ No members found for project `{project_id}`."}
			]
			return slack_response(response_url, msg_block)
		msg_block = [
			{"type": "mrkdwn", "text": f"These are the members found for project `{project_id}`."}
		]
		# member_list = "\n".join(
		# 	[f"• {m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')}" for m in members])
		for m in members:
			msg_block.append(
				{"type": "mrkdwn", "text": f"{m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')}"})
		return slack_response(response_url, msg_block)

	elif info_type == "project_details":
		msg_block = [
			{"type": "mrkdwn", "text": f"*Project ID:*\n{project_doc.name}"},
			{"type": "mrkdwn", "text": f"*Project Name:*\n{project_doc.project_name}"},
			{"type": "mrkdwn", "text": f"*Status:*\n{project_doc.status}"},
			{"type": "mrkdwn", "text": f"*Expected Start:*\n{project_doc.expected_start_date}"},
			{"type": "mrkdwn", "text": f"*Expected End:*\n{project_doc.expected_end_date}"},
			{"type": "mrkdwn", "text": f"*Customer:*\n{project_doc.customer}"}
		]
		return slack_response(response_url, msg_block)

	else:
		msg_block = [
			{"type": "mrkdwn", "text": "❌ Invalid info type. Use `members` or `project_details`."}
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
	frappe.log_error("result", result)
