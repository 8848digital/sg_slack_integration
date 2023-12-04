import frappe
import requests
import json


def validate(self, method=None):
    create_slack_channel(self)
    
def create_slack_channel(self,method=None):
    try:
        if self.is_new():
            token = frappe.db.get_single_value('Token', 'token')
            url = "https://slack.com/api/conversations.create"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            if self.doctype == "Project":
                name = self.name.lower().replace(' ', '_')
            if self.doctype == "Project Employee Distribution":
                name = self.opportunity.lower()
            data =  json.dumps({"name": name})
            response = requests.post(url, data=data, headers=headers)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Channel created successfully on Slack")
            elif not res['ok'] and res['error'] == "name_taken":
                frappe.msgprint("Channel Already exists")
            elif not res['ok']:
                frappe.log_error("POST request failed with status code: ", res)
    except Exception as e:
        frappe.throw("An error occurred: " + str(e))
