
import frappe
from frappe import _


from sg_slack_integration.doc_events.common_function import get_email_id_from_slack_user_id


@frappe.whitelist(allow_guest=True)
def get_info():

	req = frappe.request
	frappe.log_error("UAT payload", req)
	frappe.log_error("UAT Payload 2", req.form)
	text = req.form.get("text")  # slash command input
	user_id = req.form.get("user_id")  # Slack user ID

	if not text:
		return slack_response("❌ Please provide valid parameters: `/get-info [project-id] [members|project_details]`")

	parts = text.split()
	if len(parts) != 2:
		return slack_response("❌ Usage: `/get-info [project-id] [members|project_details]`")

	project_id, info_type = parts

	# Lookup Slack user_id -> ERPNext email
	slack_user_email = get_email_id_from_slack_user_id(user_id)
	if not slack_user_email:
		return slack_response("⚠️ Could not identify you in ERP system.")

	# Check if user has 'Partner' role
	user_roles = frappe.get_roles(slack_user_email)
	if "Partner" not in user_roles:
		return slack_response("🚫 You do not have permission to access project details.")

	# Fetch the project
	project_doc = ""
	if frappe.db.exists("Project", project_id):
		project_doc = frappe.get_doc("Project", project_id)
	else:
		return slack_response(f"🚫 No project found with ID `{project_id}`.")

	if info_type == "members":
		members = frappe.get_all("Project Employee Distribution Detail", filters={
		                         "parent": project_id}, fields=["employee_name", "designation", "from_date", "to_date"])
		if not members:
			return slack_response(f"ℹ️ No members found for project `{project_id}`.")
		member_list = "\n".join(
			[f"• {m.get('employee_name')} ({m.get('designation')}) - {m.get('from_date')}-{m.get('to_date')}" for m in members])
		return slack_response(f"*Project Members for {project_id}:*\n{member_list}")

	elif info_type == "project_details":
		details = f"""*Project ID:* {project_doc.name}
			*Project Name:* {project_doc.project_name}
			*Status:* {project_doc.status}
			*Expected Start:* {project_doc.expected_start_date}
			*Expected End:* {project_doc.expected_end_date}
			*Customer:* {project_doc.customer}
	"""
		return slack_response(details)

	else:
		return slack_response("❌ Invalid info type. Use `members` or `project_details`.")


def slack_response(message: str):
    # frappe.response["type"] = "ephemeral"  # or "in_channel"
    # frappe.response["response_type"] = "ephemeral"
    # frappe.response["content_type"] = "application/json"
    # frappe.response["message"] = message
    return {
        "response_type": "ephemeral",
        "text": message
    }
