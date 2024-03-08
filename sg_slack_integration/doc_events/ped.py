import frappe
import requests
import json
from sg_slack_integration.doc_events.common_function import create_slack_channel,get_channel_id,set_topic,set_description
from urllib.parse import quote


def validate(self, method=None):
    user_ids = get_users(self)
    
    if self.ped_from == "Opportunity":
        topic_and_description = frappe.get_value("Opportunity",self.opportunity,
                                                 ['title', 'name', 'expected_closing'], as_dict=1)
        is_channel_exists = create_slack_channel(self)
        channel = get_channel_id(self)
        
        if self.is_new():
            if is_channel_exists != "name_taken":
                topic = f"{topic_and_description.title}-{topic_and_description.name}"
                description = f"Expected closing Date: {str(topic_and_description.expected_closing)}"
                set_topic(self, channel, topic)
                set_description(self, channel, description)
            send_file(self, channel)
            
        invite_users(user_ids, channel)
    if user_ids:
        removed_user_slack_ids = removed_user_slack_id(self,user_ids)
        remove_member(removed_user_slack_ids, channel)
        
    if self.ped_from == "Project":
        channel = get_channel_id(self)
        if user_ids:
        	invite_users(user_ids, channel)

def send_file(self,channel):
    files = frappe.db.get_list("File",filters={'attached_to_name':self.opportunity,'attached_to_doctype':"Opportunity"},fields=['name'])
    for file in files:
        try:
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
                response = requests.post(url, data=data, files=files, headers=headers)
                res = response.json()
                if res['ok']:
                    frappe.msgprint("File sent successfully on Slack")
                else:
                    frappe.log_error("POST request failed with status code:", res)
            else:
                frappe.msgprint("Please set SLack Token First")
        except Exception as e:
            frappe.log_error("An error occurred:", str(e))

def invite_users(user_ids, channel):
    try:
        token = frappe.db.get_single_value('Token', 'token')
        if token:
            url = "https://slack.com/api/conversations.invite"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
                }   
            data = json.dumps({"users":user_ids, "channel":channel, "forced":True})
            response = requests.request("POST",url, data=data, headers=headers, )
            res = response.json()
            if res['ok']:
                frappe.msgprint("Users invited successfully")
            if not res['ok']:
                frappe.log_error(res['error'])
        else:
            frappe.msgprint("Please set Slack Token First")
    except Exception as e:
        frappe.throw("There is an error trying to invite users")
		
def get_users(self,method=None):
    slack_user_ids = ""
    if self.distribution_detail:
        for user in self.distribution_detail:
            email = frappe.db.get_value("Employee",user.employee,'company_email')
            if email:
                slack_user_id = get_user_ids(email)
                if slack_user_id:
                    slack_user_ids += slack_user_id+","
    if self.ped_from == "Opportunity":
        doc = frappe.get_doc("Opportunity",self.opportunity)
        tech_name = doc.custom_tech_name if doc.custom_tech_name else None
        proposal_manager_name = doc.custom_proposal_manager_name if doc.custom_proposal_manager_name else None
        partner_name = doc.custom_partner_name if doc.custom_partner_name else None
        users = frappe.db.get_list("Employee", filters={'name':["in", [tech_name, proposal_manager_name, partner_name]]},fields='company_email')
        if users:
            for user in users:
                slack_user_id = get_user_ids(user.company_email)
                if slack_user_id:
                    slack_user_ids += slack_user_id+","
    return slack_user_ids

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


def removed_user_slack_id(self, user_ids):
    present_user_ids = []
    remove_slack_user_ids = []
    
    ped_exist = frappe.db.exists("Project Employee Distribution", self.name)
    
    if ped_exist:
        old_doc = frappe.get_cached_doc("Project Employee Distribution", self.name)
        for user in old_doc.distribution_detail:
            email_to_remove = frappe.db.get_value("Employee",user.employee,'company_email')
            if email_to_remove:
                present_user_id = get_user_ids(email_to_remove)
                if present_user_id:
                    present_user_ids.append(present_user_id)
                    
    user_id_set = set(user_ids.split(','))
    present_user_id_set = set(present_user_ids)
    
    for remove_slack_user_id in present_user_id_set:
        if remove_slack_user_id not in user_id_set:
            remove_slack_user_ids.append(remove_slack_user_id)
            
    return remove_slack_user_ids