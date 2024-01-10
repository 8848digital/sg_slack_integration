import frappe
import requests
import json
from sg_slack_integration.doc_events.common_function import create_slack_channel,set_topic,set_description

def validate(self, method=None):
    create_slack_channel(self)
    channel = get_channel_id(self)   
    if self.is_new():
        if self.project_name:
            set_topic(self,channel, self.project_name)
        if self.customer:
            set_description(self,channel, self.customer+"-"+self.customer_name)
     

def get_channel_id(self):
    channel_name = self.name.lower().replace(' ', '_')
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