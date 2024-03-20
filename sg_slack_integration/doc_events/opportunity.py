import frappe
from sg_slack_integration.doc_events.common_function import archive_channel,get_channel_id,unarchive_channel


def validate(self,method=None):
    handle_workflow_state(self)
            

def handle_workflow_state(self):
    channel = get_channel_id(self)
    if channel:
        old_doc = frappe.get_cached_doc("Opportunity", self.name)
        previous_workflow = old_doc.workflow_state
        if self.workflow_state == "Client Approval Pending":
            archive_channel(self,channel)
        if previous_workflow == "Client Approval Pending" and self.workflow_state == "In Progress":
            unarchive_channel(self,channel)