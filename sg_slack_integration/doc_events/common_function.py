import re
import frappe
import requests
import json


def create_slack_channel(self,method=None):
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
            name = re.sub(r'[^\w\d\u0600-\u06FF-]', '', name)[:80]
            
        data =  json.dumps({"name": name, 
                            "is_private":"true"
                            })
    try:
        response = requests.post(url, data=data, headers=headers)
        res = response.json()
        if res['ok']:
            frappe.msgprint("Channel created successfully on Slack")
            return res['ok']
        elif not res['ok'] and res['error'] == "name_taken":
            frappe.msgprint("Channel Already exists")
            return res['error']
        elif not res['ok']:
            frappe.log_error("Channel creation failed with status code: ", res)
        else:
            frappe.throw("Please set Slack Token First")
    except Exception as e:
        frappe.throw("An error occurred: " + str(e))

        
def get_channel_id(self, method=None):
    if self.doctype == "Opportunity":
        channel_name = self.proposal_name.lower().replace(' ', '_')
    elif self.doctype == "Project":
        channel_name = self.name.lower().replace(' ', '_')
    elif self.doctype == "Project Employee Distribution":
        if self.ped_from == "Opportunity":
            channel_name = frappe.get_value("Opportunity", self.opportunity, "proposal_name")
            channel_name = channel_name.lower().replace(' ', '_')
        if self.ped_from == "Project":
            channel_name = self.project.lower().replace(' ','_')
            
    channel_name = re.sub(r'[^\w\d\u0600-\u06FF-]', '', channel_name)[:80]
    
    token = frappe.db.get_single_value('Token', 'token')
    
    if token:
        url = "https://slack.com/api/conversations.list"	
        headers = {	
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }   
        payload = {
            "limit": 999, 
            "types": "public_channel, private_channel"
        }
        response = requests.request("POST",url, headers=headers, data=payload)
        res = response.json()
        if res['ok']:
            for channel in res['channels']:
                if channel.get('name') == channel_name:
                    return channel.get('id')
    else:
        frappe.msgprint("Please set Slack Token First")
    
    
def set_topic(self,channel, topic):
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
        try:
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Topic set successfully on Slack")
            else:
                frappe.msgprint("Topic set unsuccessful with status code:", res)
        
        except Exception as e:
                frappe.log_error("An error occurred:", str(e))
    else:
        frappe.msgprint("Please set Slack Token First")


def set_description(self,channel, description):
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
        try:
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Description set successfully on Slack")
            else:
                frappe.msgprint("Description set Failed with status code:", res)
    
        except Exception as e:
            frappe.log_error("An error occurred:", str(e))
    else:
        frappe.msgprint("Please set Slack Token First")


def archive_channel(self,channel):
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
        try:
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Channel Archived Successfully")
            else:
                frappe.msgprint("Channel archiveing failed with status code:", res)
        except Exception as e:
                frappe.log_error("An error occurred:", str(e))
    else:
        frappe.msgprint("Please set Slack Token First")


def unarchive_channel(self,channel):
    token = frappe.db.get_single_value('Token', 'token')

    if token:
        url = 'https://slack.com/api/conversations.unarchive'
        headers = {
            'Authorization': f'Bearer {token}',
            "Content-Type": 'application/json; charset=utf-8'
        }
        payload = {
            'channel': channel,
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            res = response.json()
            if res['ok']:
                frappe.msgprint("Channel Unarchived Successfully")
            else:
                frappe.msgprint("Channel unarchiveing failed with status code: ", res)
        except Exception as e:
                frappe.log_error("An error occurred:", str(e))
    else:
        frappe.msgprint("Please set Slack Token First")

       
def send_file(self,channel):
    files = frappe.db.get_list("File",filters={'attached_to_name':self.opportunity,'attached_to_doctype':"Opportunity"},fields=['name'])
    for file in files:
        token = frappe.db.get_single_value('Token', 'token')
        if token:
            url = "https://slack.com/api/files.upload"
            headers = {
                'Authorization': f'Bearer {token}'
                }
            data = {
                'channels': channel,
                'initial_comment': 'Here is RFP file!'
                }
            file = frappe.utils.file_manager.get_file(file.name)
            files = {
                'file': (file),
                }
            try:
                response = requests.post(url, data=data, files=files, headers=headers)
                res = response.json()
                if res['ok']:
                    frappe.msgprint("File sent successfully on Slack")
                else:
                    frappe.log_error("File send unsuccessfully with status code:", res)
            except Exception as e:
                frappe.log_error("An error occurred:", str(e))
        else:
            frappe.msgprint("Please set SLack Token First")
            
            
def invite_users(user_ids, channel):
    token = frappe.db.get_single_value('Token', 'token')
    if token:
        url = "https://slack.com/api/conversations.invite"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
            }   
        data = json.dumps({"users":user_ids, "channel":channel, "forced":True})
        try:
            response = requests.request("POST",url, data=data, headers=headers, )
            res = response.json()
            if res['ok']:
                frappe.msgprint("Users invited successfully")
            if not res['ok']:
                frappe.log_error(res['error'])
        except Exception as e:
            frappe.throw("There is an error trying to invite users")
    else:
        frappe.msgprint("Please set Slack Token First")


def get_user_ids(email):
    token = frappe.db.get_single_value('Token', 'token')
    if token:
        url = "https://slack.com/api/users.lookupByEmail"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/x-www-form-urlencoded'
            }   
        data = f"email={email}"
        response = requests.request("POST",url, data=data, headers=headers)
        res = response.json()
        if res['ok']:
            return res['user'].get('id')
        else:
            frappe.log_error("Slack User not found")
            

def remove_member(user_ids_to_remove, channel_id):
    token = frappe.db.get_single_value('Token', 'token')
    
    url = f'https://slack.com/api/conversations.kick'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {token}'
    }
    for user_id_to_remove in user_ids_to_remove:
        data = {
            'channel': channel_id,
            'user': user_id_to_remove
        }
        response = requests.post(url, headers=headers, params=data)
        if response.ok:
            frappe.msgprint(f"User removed from channel")
        else:
            frappe.log_error(f"Error removing user from channel: {response.text}")