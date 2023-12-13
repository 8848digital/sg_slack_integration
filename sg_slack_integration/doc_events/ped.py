import frappe
import requests
import json
from sg_slack_integration.doc_events.project import create_slack_channel



def validate(self, method=None):
	user_ids = get_user_ids(self)
	if self.ped_from == "Opportunity":
		create_slack_channel(self)
		channel = get_channel_id(self)
		invite_users(user_ids, channel)
	if self.ped_from == "Project":
		channel = get_channel_id(self)
		invite_users(user_ids, channel)
	
		


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

def get_user_ids(self,method=None):
	user_ids = ""
	for user in self.distribution_detail:
		try:
			email = frappe.db.get_value("Employee",user.employee,'company_email')
			if not email:
				break
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
				user_ids+=(res['user'].get('id'))+","
		except Exception as e:
			frappe.throw("An error occurred: " + str(e))
	return user_ids

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
			
	


	
			
