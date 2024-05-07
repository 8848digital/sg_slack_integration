from datetime import date, timedelta
import frappe
from frappe import _

from sg_slack_integration.doc_events.common_function import (
	unarchive_channel,
)


def validate(self, method=None):
	handle_workflow_state(self)


def handle_workflow_state(self):
	if self.is_new():
		return
	channel = self.custom_channel_id
	if channel:
		opportunity_exist = frappe.db.exists("Opportunity", self.name)
		if opportunity_exist:
			old_doc = frappe.get_cached_doc("Opportunity", self.name)
			previous_workflow = old_doc.workflow_state
			if self.workflow_state == "Client Approval Pending":
				set_archiving_date(self)
			if (
				previous_workflow == "Client Approval Pending"
				and self.workflow_state == "In Progress"
				and self.custom_is_channel_archived == 1
			):
				unarchive = unarchive_channel(self, channel)
				if unarchive:
					self.custom_is_channel_archived = 0
					self.custom_archiving_date = None
			elif (
       			previous_workflow == "Client Approval Pending" 
         		and self.workflow_state == "In Progress" 
           		and self.custom_is_channel_archived == 0
            ):
				self.custom_archiving_date = None
		else:
			frappe.throw(_("Slack channel already created with same proposal name"))


def set_archiving_date(self):
    days_to_archive = frappe.db.get_single_value("Slack Integration Settings", "days_to_archive_channel")
    self.custom_archiving_date = date.today() + timedelta(days = int(days_to_archive))