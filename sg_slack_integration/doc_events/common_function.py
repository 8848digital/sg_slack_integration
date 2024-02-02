import frappe
import requests
import json

def create_slack_channel(self,method=None):
    try:
        if self.is_new():                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
            token = frappe.db.get_single_value('Token', 'token')
            if token:
                url = "https://slack.com/api/conversations.create"
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                if self.doctype == "Project":
                    name = self.name.lower().replace(' ', '_')
                if self.doctype == "Project Employee Distribution":
                    name = frappe.get_value("Opportunity", self.opportunity, "proposal_name")
                    name = name.lower().replace(' ', '_')
                    
                data =  json.dumps({"name": name})
                response = requests.post(url, data=data, headers=headers)
                res = response.json()
                if res['ok']:
                    frappe.msgprint("Channel created successfully on Slack")
                elif not res['ok'] and res['error'] == "name_taken":
                    frappe.msgprint("Channel Already exists")
                    return res['error']
                elif not res['ok']:
                    frappe.log_error("POST request failed with status code: ", res)
            else:
                frappe.throw("Please set Slack Token First")
    except Exception as e:
        frappe.throw("An error occurred: " + str(e))
        
def get_channel_id(self, method=None):
    if self.doctype == "Opportunity":
        channel_name = self.name.lower().replace(' ', '_')
    elif self.doctype == "Project":
        channel_name = self.name.lower().replace(' ', '_')
    elif self.doctype == "Project Employee Distribution":
        if self.ped_from == "Opportunity":
            channel_name = frappe.get_value("Opportunity", self.opportunity, "proposal_name")
            channel_name = channel_name.lower().replace(' ', '_')
        if self.ped_from == "Project":
            channel_name = self.project.lower().replace(' ','_')
            
    token = frappe.db.get_single_value('Token', 'token')
    
    if token:
        url = "https://slack.com/api/conversations.list"	
        headers = {	
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }   
        payload = {"limit": 999}
        response = requests.request("POST",url, headers=headers, data=payload)
        res = response.json()
        if res['ok']:
            for channel in res['channels']:
                if channel.get('name') == channel_name:
                    return channel.get('id')
    else:
        frappe.msgprint("Please set Slack Token First")
        
def set_topic(self,channel, topic):
    try:
        token = frappe.db.get_single_value('Token', 'token')
        if token:
            url = "https://slack.com/api/conversations.setTopic"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            payload = {
                'channel': channel,
                'topic': topic,
            }
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Topic set successfully on Slack")
            else:
                frappe.msgprint("POST request failed with status code:", res)
        else:
            frappe.msgprint("Please set Slack Token First")
    except Exception as e:
            frappe.log_error("An error occurred:", str(e))

def set_description(self,channel, description):
    try:
        token = frappe.db.get_single_value('Token', 'token')
        
        if token:
            url = 'https://slack.com/api/conversations.setPurpose'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
            }
            payload = {
                'channel': channel,
                'purpose': description,
            }
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Description set successfully on Slack")
            else:
                frappe.msgprint("POST request failed with status code:", res)
        else:
            frappe.msgprint("Please set Slack Token First")
    except Exception as e:
            frappe.log_error("An error occurred:", str(e))

def archive_channel(self,channel):
    try:
        token = frappe.db.get_single_value('Token', 'token')
        
        if token:
            url = 'https://slack.com/api/conversations.archive'
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Authorization': f'Bearer {token}',
            }
            payload = {
                'channel': channel,
            }
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Channel Archived Successfully")
            else:
                frappe.msgprint("POST request failed with status code:", res)
        else:
            frappe.msgprint("Please set Slack Token First")
    except Exception as e:
            frappe.log_error("An error occurred:", str(e))
