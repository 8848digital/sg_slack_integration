import frappe
import requests
import json
from sg_slack_integration.doc_events.project import create_slack_channel
from urllib.parse import quote



def validate(self, method=None):
	user_ids = get_users(self)
	if self.ped_from == "Opportunity":
		create_slack_channel(self)
		channel = get_channel_id(self)
		invite_users(user_ids, channel)
		send_file(self, channel)
	if self.ped_from == "Project":
		channel = get_channel_id(self)
		invite_users(user_ids, channel)

def send_file(self,channel):
	files = frappe.db.get_list("File",filters={'attached_to_name':self.opportunity,'attached_to_doctype':"Opportunity"},fields=['name'])
	for file in files:
		try:
			token = frappe.db.get_single_value('Token', 'token')
			url = "https://slack.com/api/files.upload"
			headers = {
				'Authorization': f'Bearer {token}',
			}
			data = {
				'channels': channel,
				'initial_comment': 'Here is a File!'
			}
			
			file = frappe.utils.file_manager.get_file(file.name)
			files = {
				'file': (file),
			}
			response = requests.post(url, data=data, files=files, headers=headers)
			res = response.json()
			if res['ok']:
				print("Image sent successfully on Slack")
			else:
				print("POST request failed with status code:", res)
		except Exception as e:
			print("An error occurred:", str(e))

def invite_users(user_ids, channel):
	try:
		token = frappe.db.get_single_value('Token', 'token')
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
			frappe.msgprint(res['error'])
	except Exception as e:
		frappe.throw("There is an error trying to invite users")
		
def get_users(self,method=None):
	slack_user_ids = ""
	for user in self.distribution_detail:
		email = frappe.db.get_value("Employee",user.employee,'company_email')
		if email:
			slack_user_id = get_user_ids(email)
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

def get_channel_id(self, method=None):
	if self.ped_from == "Opportunity":
		channel_name = self.opportunity.lower()
	if self.ped_from == "Project":
		channel_name = self.project.lower().replace(' ','_')
	token = frappe.db.get_single_value('Token', 'token')
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
			



	


	
			
