import re
import frappe



def compatible_slack_channel_name(channel_name):
    if not channel_name:
        return
    settings_doc = frappe.get_doc("Slack Integration Settings").as_dict()
    special_character = settings_doc.get("special_character_replacement")

    channel_name = channel_name.lower().replace(" ", "_")
    channel_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", channel_name)

    for character in special_character:
        if character["not_compatible"] in channel_name:
            channel_name = channel_name.replace(character["not_compatible"], character["compatible"])

    channel_name = channel_name[:75]
    return channel_name


def create_slack_log(self, status, details=None, error=None):
	from sg_slack_integration.doc_events.common_function import create_slack_channel_detail

	new_doc = frappe.new_doc("Slack Log")
	new_doc.against_doctype = self.doctype
	new_doc.doc_name = self.name
	new_doc.status = status
	if not error:
		if details is not None:
			new_doc.custom_channel_id = details.get("id", "")
			new_doc.custom_channel_name = details.get("name", "")
			if new_doc.custom_channel_id:
				create_slack_channel_detail(details=details)
				new_doc.custom_link_to_channel = new_doc.custom_channel_id
	if error:
		new_doc.error_response = error
	new_doc.insert(ignore_permissions=True)


def create_slack_log_for_commands(user, status, cmd, param, response, error=None):
	if cmd and param and status:
		new_doc = frappe.new_doc("Slack Log")
		new_doc.status = status
		new_doc.custom_slack_poll_type = "Command"
		new_doc.custom_command = cmd
		new_doc.custom_parameters = param
		new_doc.custom_user = user
		if not error:
			new_doc.custom_slack_poll_result = response
		if error:
			new_doc.error_response = error
		new_doc.insert(ignore_permissions=True)
