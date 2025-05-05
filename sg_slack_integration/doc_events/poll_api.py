

import frappe
import json
import requests

def post_poll_to_slacks(slack_token, payload,doctype=None, email=None):
	url = "https://slack.com/api/chat.postMessage"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json",
	}
	response = requests.post(url, headers=headers, json=payload)
	frappe.log_error("Error in Poll Post", response.json())
	if not response.json().get("ok"):
		create_slack_log_for_poll(self=doctype, status="Error",
		                          poll_type="Send Poll", error=str(response.json()))
		print("Failed to post poll:", response.json())
	else:
		if doctype and email:
			result = response.json()
			message = f"{result.get('message').get('text')} triggered to {email}\n{str(result.get('message').get('blocks'))}"
			create_slack_log_for_poll(
					self=doctype, status="Success", poll_type="Send Poll", poll_result=message)
		print("Poll posted successfully:", response.json())
		


def get_user_id_by_email(email, slack_token):
	"""
	Retrieve Slack User ID by email.
	"""
	url = "https://slack.com/api/users.lookupByEmail"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json"
	}

	params = {
	"email":email
	}
	response = requests.get(url, headers=headers, params=params)
	data = response.json()
	if data.get("ok"):
		return data["user"]["id"]
	else:
		frappe.errprint(data.get('error'))
		return None
	

def get_question_from_payload(payload, block_id):
    message_blocks = payload.get("message", {}).get("blocks", "")
    for i, block in enumerate(message_blocks):
        if block.get("block_id") == block_id and i > 0:
            prev_block = message_blocks[i - 1]
            if prev_block.get("type") == "section" and "text" in prev_block:
                return prev_block["text"]["text"]

    return None 


def send_ephemeral_message(slack_token, channel_id, user_id, ts, selected_option, blocks, block_id, poll_id):
	"""Update the Slack message to indicate the selected option."""

	updated_blocks = []
	frappe.log_error("Error in slack", blocks)
	for block in blocks:
		if block.get("type") == "actions" and block.get("block_id") == block_id:
			# Update the style of the selected button
			# updated_elements = []
			options_text = ""
			for element in block.get("elements", []):
				label = element["text"]["text"]
				if element.get("value") == selected_option:
					options_text += f"• ✔ *{label}*\n"
				else:
					options_text += f"• {label}\n"

			updated_blocks.append({
				"type": "section",
				"text": {
					"type": "mrkdwn",
					"text": f"*You selected:*\n{options_text}"
				}
			})
		# 	for element in block.get("elements", []):
		# 		if element.get("type") == "button":
		# 			# element["disabled"] = True
		# 			# Check if this option is selected
		# 			if element.get("value") == selected_option:
		# 				# Highlight the selected option
		# 				element["style"] = "primary"  # Set to primary to indicate selection
		# 				element["text"]["text"] = f"✔ {element['text']['text']}"  # Add a checkmark or any indicator
		# 			else:
		# 				# Reset other options
		# 				element.pop("style", None)  # Remove any style from unselected options
		# 			updated_elements.append(element)
		# 	block["elements"] = updated_elements
		# updated_blocks.append(block)

	# Make the API call to update the message
	url = "https://slack.com/api/chat.update"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json",
	}

	payload = {
		"channel": channel_id,
		"ts": ts,
		"text": poll_id,
		"blocks": updated_blocks,
	}
	

	response = requests.post(url, headers=headers, json=payload)
	
	if not response.json().get("ok"):
		frappe.log_error(f"Error updating message: ",response.json())
		return None

	return response.json()


def create_slack_log_for_poll(self, status, poll_type=None, poll_result=None, error=None):
	new_doc = frappe.new_doc("Slack Log")
	new_doc.against_doctype = self.doctype
	new_doc.doc_name = self.name
	new_doc.status = status
	new_doc.custom_slack_poll_type = poll_type
	new_doc.custom_slack_poll_result = poll_result
	if error:
		new_doc.error_response = error
	new_doc.insert(ignore_permissions=True)



def send_confirmation_message(slack_token,doctype=None, email=None):
	response_data=[{
		"type": "section",
		"text": {"type": "mrkdwn", "text": "* Your response has been submitted successfully! :white_check_mark: *"}
	}]
	user_id = get_user_id_by_email(email, slack_token)
	payload ={
		"type": doctype.name,
		"blocks": response_data
	}
	payload["channel"] = user_id
	url = "https://slack.com/api/chat.postMessage"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json",
	}

	response = requests.post(url, headers=headers, json=payload)
	frappe.log_error(f"Slack Confirmation message {doctype.doctype}", response.json())
	if not response.json().get("ok"):
		create_slack_log_for_poll(self=doctype, status="Error",
		                          poll_type="Confirmation Message", error=str(response.json()))
		print("Failed to post poll:", response.json())
	else:
		if doctype and email:
			result = response.json()
			message = f"{result.get('message').get('text')} triggered to {email}\n{str(result.get('message').get('blocks'))}"
			create_slack_log_for_poll(
					self=doctype, status="Success", poll_type="Confirmation Message", poll_result=message)
		print("Poll posted successfully:", response.json())