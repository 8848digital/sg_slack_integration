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

def create_slack_log(self, status, error=None):
	new_doc = frappe.new_doc("Slack Log")
	new_doc.against_doctype = self.doctype
	new_doc.doc_name = self.name
	new_doc.status = status

	if error:
		new_doc.error_response = error
	new_doc.insert(ignore_permissions=True)