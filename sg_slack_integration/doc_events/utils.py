import frappe


def create_slack_log(self, status, error=None):
	new_doc = frappe.new_doc("Slack Log")
	new_doc.against_doctype = self.doctype
	new_doc.doc_name = self.name
	new_doc.status = status

	if error:
		new_doc.error_response = error
	new_doc.insert(ignore_permissions=True)