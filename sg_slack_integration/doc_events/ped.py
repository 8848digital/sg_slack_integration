import frappe
import requests
import json
def invite_users(self, method=None):
	user_ids = get_user_ids(self)
	channel = get_channels(self)
	try:
		token = frappe.db.get_single_value('Token', 'token')
		url = "https://slack.com/api/conversations.invite"
		headers = {
			'Authorization': f'Bearer {token}',
			'Content-Type': 'application/json'
		}   
		data = json.dumps({"users":user_ids, "channel":channel})
		response = requests.request("POST",url, data=data, headers=headers)
		res = response.json()
		if res['ok']:
			frappe.msgprint("Users successfully invited")
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

def get_channels(self, method=None):
	token = frappe.db.get_single_value('Token', 'token')
	url = "https://slack.com/api/conversations.list"
	headers = {
		'Authorization': f'Bearer {token}',
		'Content-Type': 'application/x-www-form-urlencoded'
	}   
	response = requests.request("POST",url, headers=headers)
	res = response.json()
	if res['ok']:
		for channel in res['channels']:
			if channel.get('name') == self.project_name.lower().replace(' ','_'):
				return channel.get('id')
	


	
			
