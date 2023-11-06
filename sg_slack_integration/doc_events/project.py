import frappe
import requests
import json

def create_slack_channel(self,method=None):
    try:
        if self.is_new():
            token = frappe.db.get_single_value('Token', 'token')
            url = "https://slack.com/api/conversations.create"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }   
            data =  json.dumps({"name": self.project_name.lower().replace(' ', '_')})
            response = requests.post(url, data=data, headers=headers)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Channel created successfully on Slack")
            else:
                return "POST request failed with status code: " + str(response.status_code)
    except Exception as e:
        frappe.throw("An error occurred: " + str(e))

