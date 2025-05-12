from sg_slack_integration.doc_events.poll_api import send_ephemeral_message
import frappe
import requests
import json




def send_poll_for_employee_profile(status=None):
	slack_token = frappe.db.get_single_value(
		"Slack Integration Settings", "employee_profile_token")
	emp_list = []
	if status is None:
		emp_list = frappe.get_all("Employee Profile", ["name", "employee_id"])
	else:
		emp_list = frappe.get_all(
			"Employee Profile", {"workflow_state": ["in", status]})

	for each in emp_list:
		start_poll(each.get('name'), each.get('employee_id'), slack_token)


@frappe.whitelist()
def start_poll(doc_name, slack_token):
	doctype = "Employee Profile"
	doc = ""
	doc = frappe.get_doc(doctype, doc_name)
	poll_receiver_emp_id = doc.employee_id

	questions_and_answers = []
	# POLL Receiver's user id
	poll_receiver_user_id = frappe.db.get_value(
		'Employee', poll_receiver_emp_id, 'user_id')

	header_block = {
		"type": "header",
		"text": {"type": "plain_text", "text": f'Hi {doc.employee_name}', "emoji": True}
	}

	questions_and_answers.append(header_block)

	# description_block = {
	#             "type": "section",
	#         				"text": {"type": "mrkdwn", "text": doc.context}
	# }
	# questions_and_answers.append(description_block)

	question_text = f'How many years to total work experience do you have?'
	options = ["1+", "3+", "5+", "10+", "12+", "15+"]

	# Add question block
	question_block = {
		"type": "section",
		"block_id": f"question_{len(questions_and_answers)}",
		"text": {"type": "mrkdwn", "text": f"*{question_text}*"}
	}
	questions_and_answers.append(question_block)

	# Add answer block
	answer_elements = []
	for each in options:
		answer_elements.append({
			"type": "button",
			"text": {"type": "plain_text", "text": each},
			"value": each,
			"style": "primary"
		})

	# Add the answer block element
	answer_block = {
		"type": "actions",
		"block_id": f"answer_{len(questions_and_answers)}",
		"elements": answer_elements
	}

	questions_and_answers.append(answer_block)

	# Generate the Body
	payload = {
		"text": doc.name,
		"blocks": questions_and_answers
	}

	# user_emails = [poll_receiver_user_id]
	user_emails = ["saffaat@8848digital.com"]

	for email in user_emails:
		user_id = get_user_id_by_email(email, slack_token)
		if user_id:
			payload = payload.copy()
			payload["channel"] = user_id
			post_poll_to_slacks(slack_token, payload, doctype=doc, email=email)


@frappe.whitelist(allow_guest=True)
def handle_poll_response():
	try:
		payload = frappe.request.form.get("payload")
		if not payload:
			frappe.log_error("Slack Poll | Handle Response | error in format")
			return {"error": "Invalid payload format."}

		slack_data = json.loads(payload)
		frappe.log_error(
			"Slack Poll | Handle Poll Response | Response", str(slack_data))

		user_id = slack_data.get("user", {}).get("username")
		channel_id = slack_data.get("channel", {}).get("id")
		action = slack_data.get("actions", [])[0]
		block_id = action.get("block_id", "")
		poll_id = slack_data.get("message", {}).get("text", "")
		selected_option = action.get("value")
		# get_mail = get_slack_user_details( slack_data.get("user", {}).get("id"), slack_token)
		ts = slack_data.get("message", {}).get("ts", "")

		# Identify the doctype
		doctype = "Employee Profile"
		token = "bday_bot_token"

		slack_token = frappe.db.get_single_value("Slack Integration Settings", token)

		emp_prof = frappe.db.exists(doctype, {"name": poll_id})

		if emp_prof:
			emp_profile_doc = frappe.get_doc(doctype, emp_prof)
			frappe.set_user("Administrator")

			emp_profile_doc.total_exp = selected_option
			emp_profile_doc.flags.ignore_validate = True
			emp_profile_doc.flags.ignore_mandatory = True
			emp_profile_doc.save(ignore_permissions=True)
			send_ephemeral_message(
				slack_token, channel_id, user_id, ts, selected_option, slack_data.get(
					"message", {}).get("blocks", ""), block_id, poll_id
			)
			poll_message = f"Response Received for Employee Profile : {poll_id} \Experience - {str(selected_option)}"
			create_slack_log_for_poll(self=emp_profile_doc, status="Success",
			                          poll_type="Receive Response", poll_result=poll_message)

		return {"text": f"Vote for '{str(selected_option)}' recorded."}
	except Exception as e:
		frappe.log_error("Slack Poll | Error in slack", frappe.get_traceback(e))


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
            "email": email
	}
	response = requests.get(url, headers=headers, params=params)
	data = response.json()
	if data.get("ok"):
		return data["user"]["id"]
	else:
		frappe.errprint(data.get('error'))
		return None


def post_poll_to_slacks(slack_token, payload, doctype=None, email=None):
	url = "https://slack.com/api/chat.postMessage"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json",
	}

	response = requests.post(url, headers=headers, json=payload)
	frappe.log_error(f"Slack Poll Posting to {email}", response.json())
	if not response.json().get("ok"):
		create_slack_log_for_poll(self=doctype, status="Error",
		                          poll_type="Send Poll", error=str(response.json()))
	else:
		result = response.json()
		if doctype and email:
			# frappe.log_error("response", result.get('message').get('blocks'))
			message = f"{result.get('message').get('text')} triggered to {email}\n{str(result.get('message').get('blocks'))}"
			create_slack_log_for_poll(
				self=doctype, status="Success", poll_type="Send Poll", poll_result=message)


def get_question_from_payload(payload, block_id):
    message_blocks = payload.get("message", {}).get("blocks", "")
    for i, block in enumerate(message_blocks):
        if block.get("block_id") == block_id and i > 0:
            prev_block = message_blocks[i - 1]
            if prev_block.get("type") == "section" and "text" in prev_block:
                return prev_block["text"]["text"]

    return None


def get_slack_user_details(user_id, slack_token):
	url = "https://slack.com/api/users.info"
	headers = {
		"Authorization": f"Bearer {slack_token}"
	}
	params = {
		"user": user_id
	}

	try:
		response = requests.get(url, headers=headers, params=params)
		response_data = response.json()

		if response_data.get("ok"):
			user_info = response_data.get("user")
			email = user_info.get("profile", {}).get("email")
			slack_id = user_info.get("id")
			return {
				"email": email,
				"slack_id": slack_id,
			}
		else:
			return {"error": response_data.get("error")}
	except requests.exceptions.RequestException as e:
		return {"error": f"Request error: {str(e)}"}


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
