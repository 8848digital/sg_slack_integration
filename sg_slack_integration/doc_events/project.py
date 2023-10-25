import frappe
import requests
import json

def create_slack_channel(self,method=None):
    try:
        if self.new():
            frappe.msgprint('Creating slack channel')
            token = frappe.db.get_single_value('Token', 'token')
            url = "https://slack.com/api/conversations.create"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }   
            data =  json.dumps({"name": self.project_name.lower()})
            print(data)
            response = requests.post(url, data=data, headers=headers)
            print(response.text)
            if response.status_code == 200:
                return "Channel created successfully on Slack"
            else:
                return "POST request failed with status code: " + str(response.status_code)
    except Exception as e:
        return "An error occurred: " + str(e)



def send_req():
    url = "https://slack.com/api/conversations.create"

    payload = json.dumps({
    "name": "testing"
    })
    headers = {
    'Authorization': 'Bearer xoxp-5620465230965-6049054922738-6081105257539-51330b37ca45b1c0b791e452df38a0cd',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
