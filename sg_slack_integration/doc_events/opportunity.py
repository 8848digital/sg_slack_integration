import frappe
from frappe import _

from sg_slack_integration.doc_events.common_function import (
	archive_channel,
	get_channel_id,
	unarchive_channel,
)


def validate(self, method=None):
	handle_workflow_state(self)


def handle_workflow_state(self):
	if self.is_new():
		return
	channel = get_channel_id(self)
	if channel:
		opportunity_exist = frappe.db.exists("Opportunity", self.name)
		if opportunity_exist:
			old_doc = frappe.get_cached_doc("Opportunity", self.name)
			previous_workflow = old_doc.workflow_state
			if self.workflow_state == "Client Approval Pending":
				archive_channel(self, channel)
			if (
				previous_workflow == "Client Approval Pending"
				and self.workflow_state == "In Progress"
			):
				unarchive_channel(self, channel)
		else:
			frappe.throw(_("Slack channel already created with same proposal name"))