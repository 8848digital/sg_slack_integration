import frappe
import requests
import json
from sg_slack_integration.doc_events.ped import set_topic,set_description, get_channel_id


def validate(self, method=None):
    topic_and_description = frappe.get_value("Project",self.name,['project_name', 'customer'])
    create_slack_channel(self)
    channel = get_channel_id(self)
    set_topic(self,channel, topic_and_description.project_name)
    set_description(self,channel, topic_and_description.customer)
     
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
