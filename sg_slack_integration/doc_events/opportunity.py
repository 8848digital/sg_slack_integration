import frappe
import requests
from sg_slack_integration.doc_events.common_function import archive_channel,get_channel_id

def validate(self,method=None):
    channel = get_channel_id(self) 
    if channel:
        if self.workflow_state == "Client Approval Pending":
            archive_channel(self,channel)
    else:
        frappe.msgprint("Channel does not existes")