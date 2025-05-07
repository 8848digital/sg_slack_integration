import frappe
import json
# import requests
from frappe.model.workflow import apply_workflow
from frappe.core.doctype.version.version import get_diff

from sg_slack_integration.doc_events.poll_api import *


def after_insert(self, method=None):
	if self.party_type == 'Supplier':
		# old_doc = self.get_doc_before_save()
		# if old_doc:
		# 	if old_doc.worflow_state != self.workflow_state and self.workflow_state == "Approved By Project Lead":
		if self.custom_project_name:
			approver = frappe.db.get_value(
				"Project", self.custom_project_name, "custom_project_lead_email")
			# approver = "saffaat@8848digital.com"
			if approver:
				options = ["Approve", "Reject"]
				frappe.log_error("calling poll sme")
				post_sme_contract_partner_approval(
					approver=approver, options=options, doc_name=self.name)
			else:
				frappe.log_error(
					f"Slack Poll - Contract {self.name}", "Partner Email not found in Project", "Contract", self.name)
		else:
			frappe.log_error(
				f"Slack Poll - Contract {self.name}", "Project Name not found in Contract", "Contract", self.name)


# def on_update(self, method=None):
# 	pass
# 	doc_to_compare = self._doc_before_save
# 	if doc_to_compare:
# 		current_doc_changes = get_diff(doc_to_compare, self)
# 		frappe.log_error("hnages", str(current_doc_changes))
# 		if current_doc_changes and current_doc_changes.get("row_changed"):
# 			for i in current_doc_changes.get("row_changed"):
# 				if i and i[0] == "custom_contract_item":
# 					row_no = i[1]
# 					change_row = i[3]
# 					for x in change_row:
# 						if x[0] == "custom_send_for_approval" and x[1] == 0 and x[2] == 1:
# 							if self.custom_contract_item[row_no].sme_item == 0:

# 								send_poll_on_slack_for_approve(
# 									docname=i[2], project=self.custom_project_name)


def on_update_after_submit(self, method=None):
	frappe.log_error("on update after submit")
	doc_to_compare = self._doc_before_save
	if doc_to_compare:
		current_doc_changes = get_diff(doc_to_compare, self)
		frappe.log_error("hnages", str(current_doc_changes))
		if current_doc_changes and current_doc_changes.get("row_changed"):
			for i in current_doc_changes.get("row_changed"):
				if i and i[0] == "custom_contract_item":
					frappe.log_error("40")
					row_no = i[1]
					change_row = i[3]
					for x in change_row:
						if x[0] == "custom_send_for_approval" and x[1] == 0 and x[2] == 1:
							if self.custom_contract_item[row_no].sme_item == 0:
								frappe.log_error("trigger_function")
								send_poll_on_slack_for_approve(
									docname=i[2], project=self.custom_project_name)


def post_sme_contract_partner_approval(approver, options, doc_name):
	doc = frappe.get_doc('Contract', doc_name)
	poll_enabled = frappe.db.get_single_value(
		"Slack Integration Settings", 'enable_poll')
	if poll_enabled:
		slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'sme_contract_token')
		if slack_token and len(slack_token) > 0:
			header_block = {
				"type": "header",
				"text": {"type": "plain_text", "text": 'SME Contract Requires Approval: ' + doc.custom_full_name + ' - ' + doc.name}
			}
			questions_and_answers = []
			questions_and_answers.append(header_block)
			sections = [
				{"title": "Contract No", "content": doc.name},
				{"title": "Supplier Name", "content": doc.custom_full_name},
				{"title": "Start Date", "content": doc.start_date},
				{"title": "End Date", "content": doc.end_date},
				{"title": "Project", "content": doc.custom_project_name},
				{"title": "Amount", "content": doc.custom_total_amount},
				{"title": 'Form Reference', 'content': frappe.utils.get_url_to_form(
					doc.doctype, doc.name)},
			]

			for section in sections:
				description_block = {
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"*{section['title']}*:  *{section['content']}*" if section.get('title') != 'Form Reference' else f"*{section['title']}*: {section['content']}"
					},
				}
				questions_and_answers.append(description_block)
			question_text = 'Your Action on Contract'
			# for val in options:
			question_block = {
				"type": "section",
				"block_id": f"question_{len(questions_and_answers) + 1}",
				"text": {"type": "mrkdwn", "text": f"*{question_text}*"}
			}
			questions_and_answers.append(question_block)
			answer_elements = [
				{
					"type": "button",
					"text": {"type": "plain_text", "text": option.strip()},
					"value": option.strip(),
					"style": "primary" if option == "Approve" else "danger"
				}
				for option in options
			]
			answer_block = {
				"type": "actions",
				"block_id": f"answer_{len(questions_and_answers) // 2 + 1}",
				"elements": answer_elements
			}
			questions_and_answers.append(answer_block)
			payload = {
				"text": doc.name,
				"blocks": questions_and_answers
			}
			user_emails = [approver]
			# user_emails = ['saffaat@8848digital.com']
			for email in user_emails:
				user_id = get_user_id_by_email(email, slack_token)
				if user_id:
					payload = payload.copy()
					payload["channel"] = user_id
					post_poll_to_slacks(slack_token, payload, doc, approver)

# from sg_slack_integration.doc_events.sme_contract
# sg_slack_integration.sg_slack_integration.doc_events.sme_contract.handle_poll_response
@frappe.whitelist(allow_guest=True)
def handle_poll_response():
	try:
		slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'sme_contract_token')
		if not slack_token:
			return
		payload = frappe.request.form.get("payload")
		if not payload:
			frappe.log_error("error in format")
			return {"error": "Invalid payload format."}

		slack_data = json.loads(payload)
		frappe.log_error("Response for contract", str(slack_data))
		user_id = slack_data.get("user", {}).get("username")
		channel_id = slack_data.get("channel", {}).get("id")
		action = slack_data.get("actions", [])[0]
		block_id = action.get("block_id", "")
		poll_id = slack_data.get("message", {}).get("text", "")
		selected_option = action.get("value")
		# get_mail = get_slack_user_details( slack_data.get("user", {}).get("id"), slack_token)
		ts = slack_data.get("message", {}).get("ts", "")

		if poll_id and selected_option:
			if "item_" in poll_id:
				child_doc = ""
				poll_id = poll_id.split("_")
				child_doc = frappe.get_doc('Contract Item', poll_id[1])
				poll_id = poll_id[1]
				project_name = frappe.db.get_value(
					"Contract", child_doc.parent, "custom_project_name")
				if selected_option.lower() == "approve":
					frappe.log_error("got contract child")
					# parent_contract = frappe.db.get_value("Contract Item", poll_id, "parent")
					approver = frappe.db.get_value(
						"Project", project_name, "custom_project_lead_email")
					if approver:
						frappe.set_user(approver)
						parent_doc = frappe.get_doc("Contract", child_doc.parent)
						for each in parent_doc.custom_contract_item:
							if each.name == child_doc.name:
								each.sme_item = 1
								break
						# frappe.db.set_value("Contract Item", poll_id, "sme_item", 1)
						parent_doc.save(ignore_permissions=True)

						# return {"text": f"Response Recorded for '{selected_option}' recorded."}
					else:
						frappe.log_error("Slack Poll | Handle Response",
						                 "Contract Item Approver not set")
						# return {"text": f"Approver not set."}
				else:
					# send slack message to project manager.
					manager = frappe.db.get_value(
						"Project", project_name, "custom_project_manager_email")
					send_reject_response_to_manager(
						project_manager=manager, slack_token=slack_token, child_doc=child_doc, slack_data=slack_data)

				send_ephemeral_message(
                                    slack_token, channel_id, user_id, ts, selected_option, slack_data.get(
                                        "message", {}).get("blocks", ""), block_id, poll_id
                                )
				send_confirmation_message(slack_token, child_doc, approver)
				poll_message = f"Response Received for Contract Item - {poll_id}\n - {selected_option}"
				create_slack_log_for_poll(self=child_doc, status="Success",
				                          poll_type="Receive Response", poll_result=poll_message)

			else:

				doc = frappe.get_doc('Contract', poll_id)
				frappe.log_error("got contract")
				approver = ''
				project_name = doc.custom_project_name
				approver = frappe.db.get_value(
					"Project", project_name, "custom_project_lead_email")

				if approver:
					frappe.set_user(approver)
					apply_workflow(doc, selected_option)
					send_ephemeral_message(
						slack_token, channel_id, user_id, ts, selected_option, slack_data.get(
							"message", {}).get("blocks", ""), block_id, poll_id
					)
					send_confirmation_message(slack_token, doc, approver)
					poll_message = f"Response Received for Contract - {poll_id}\n - {selected_option}"
					create_slack_log_for_poll(self=doc, status="Success",
                                            poll_type="Receive Response", poll_result=poll_message)

					return {"text": f"Response Recorded for '{selected_option}' recorded."}
				else:
					return {"text": f"Approver not set."}
	except Exception as e:
		create_slack_log_for_poll(
			self=doc, status="Error", poll_type="Receive Response", error=str(frappe.get_traceback(e)))
		frappe.log_error("Error in slack", frappe.get_traceback(e))


@frappe.whitelist()
def send_poll_on_slack_for_approve(docname, project):
	#   child_doc = frappe.get_doc("Contract Item", docname)
	approver = frappe.db.get_value(
		"Project", project, "custom_project_lead_email")
	options = ["Approve", "Reject"]
	frappe.log_error("approver", approver)
	post_item_approval_on_slack(approver, options, docname)


def post_item_approval_on_slack(approver, options, doc_name):
	frappe.log_error("COntrat Item Poll")
	child_doc = frappe.get_doc('Contract Item', doc_name)
	doc = frappe.get_doc("Contract", child_doc.parent)
	poll_enabled = frappe.db.get_single_value(
		"Slack Integration Settings", 'enable_poll')
	if poll_enabled:
		slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'sme_contract_token')
		if slack_token and len(slack_token) > 0:
			frappe.log_error("sending")
			header_block = {
				"type": "header",
				"text": {"type": "plain_text", "text": 'SME Contract Item Requires Approval: ' + doc.custom_full_name + ' - ' + doc.name}
			}
			questions_and_answers = []
			questions_and_answers.append(header_block)
			sections = [
				{"title": "Contract No", "content": doc.name},
				{"title": "Supplier Name", "content": doc.custom_full_name},
				{"title": "Start Date", "content": doc.start_date},
				{"title": "End Date", "content": doc.end_date},
				{"title": "Project", "content": doc.custom_project_name},
				{"title": "Item Name", "content": child_doc.item_name},
				{"title": "Currency", "content": child_doc.custom_currency},
				{"title": "Description", "content": child_doc.description},
				{"title": "Qty", "content": child_doc.qty},
				{"title": "Rate", "content": child_doc.rate},
				{"title": "Total", "content": child_doc.total},
				{"title": "Total Contract Amount", "content": doc.custom_total_amount},
				{"title": 'Form Reference', 'content': frappe.utils.get_url_to_form(
					"Contract", doc.name)},
			]

			for section in sections:
				description_block = {
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"*{section['title']}*:  *{section['content']}*" if section.get('title') != 'Form Reference' else f"*{section['title']}*: {section['content']}"
					},
				}
				questions_and_answers.append(description_block)
			question_text = 'Your Action on Contract Item'
			# for val in options:
			question_block = {
				"type": "section",
				"block_id": f"question_{len(questions_and_answers) + 1}",
				"text": {"type": "mrkdwn", "text": f"*{question_text}*"}
			}
			questions_and_answers.append(question_block)
			answer_elements = [
				{
					"type": "button",
					"text": {"type": "plain_text", "text": option.strip()},
					"value": option.strip(),
					"style": "primary" if option == "Approve" else "danger"
				}
				for option in options
			]
			answer_block = {
				"type": "actions",
				"block_id": f"answer_{len(questions_and_answers) // 2 + 1}",
				"elements": answer_elements
			}
			questions_and_answers.append(answer_block)
			payload = {
				"text": "item_"+child_doc.name,
				"blocks": questions_and_answers
			}
			user_emails = [approver]
			# user_emails = ["saffaat@8848digital.com"]
			frappe.log_error("sending ready")
			for email in user_emails:
				user_id = get_user_id_by_email(email, slack_token)
				if user_id:
					payload = payload.copy()
					payload["channel"] = user_id
					post_poll_to_slacks(slack_token, payload, doc, approver)


def send_reject_response_to_manager(project_manager, slack_token, child_doc, slack_data):
	user_id = get_user_id_by_email(project_manager, slack_token)
	header_block = {
            "type": "header",
        				"text": {"type": "plain_text", "text": 'SME Contract Item Rejected: ' + child_doc.parent}
	}
	parent_doc = frappe.get_doc("Contract", child_doc.parent)
	questions_and_answers = []
	questions_and_answers.append(header_block)
	sections = [
		{"title": "Contract No", "content": parent_doc.name},
		{"title": "Supplier Name", "content": parent_doc.custom_full_name},
		{"title": "Start Date", "content": parent_doc.start_date},
		{"title": "End Date", "content": parent_doc.end_date},
		{"title": "Project", "content": parent_doc.custom_project_name},
		{"title": "Amount", "content": parent_doc.custom_total_amount},
		{"title": "Item", "content": child_doc.item_name},
		{"title": 'Form Reference', 'content': frappe.utils.get_url_to_form(
			parent_doc.doctype, parent_doc.name)},
		{"title": 'Rejected By - ', 'content': slack_data.get('user').get('name')},
	]

	for section in sections:
		description_block = {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*{section['title']}*:  *{section['content']}*" if section.get('title') != 'Form Reference' else f"*{section['title']}*: {section['content']}"
			},
		}
		questions_and_answers.append(description_block)

	# message = f"Partner - {slack_data.get('user').get('name')} has Rejected the Contract Item {child_doc.item_name} of value - {child_doc.total} in Contract - {child_doc.parent}\nForm Reference-{frappe.utils.get_url_to_form('Contract', child_doc.parent)}"

	payload = {
		"text": parent_doc.name,
		"blocks": questions_and_answers,
		"channel": user_id
	}
	url = "https://slack.com/api/chat.postMessage"
	headers = {
		"Authorization": f"Bearer {slack_token}",
		"Content-Type": "application/json",
	}
	response = requests.post(url, headers=headers, json=payload)

@frappe.whitelist(allow_guest=True)
def handle_poll_response_item():
	try:
		slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'sme_contract_token')
		if not slack_token:
			return
		payload = frappe.request.form.get("payload")
		if not payload:
			frappe.log_error("error in format")
			return {"error": "Invalid payload format."}

		slack_data = json.loads(payload)
		user_id = slack_data.get("user", {}).get("username")
		channel_id = slack_data.get("channel", {}).get("id")
		action = slack_data.get("actions", [])[0]
		block_id = action.get("block_id", "")
		poll_id = slack_data.get("message", {}).get("text", "")
		selected_option = action.get("value")
		# get_mail = get_slack_user_details( slack_data.get("user", {}).get("id"), slack_token)
		ts = slack_data.get("message", {}).get("ts", "")
		child_doc = ""
		if poll_id and selected_option:
			if "item_" in poll_id:
				poll_id = poll_id.split("_")
				child_doc = frappe.get_doc('Contract Item', poll_id[1])
				# parent_contract = frappe.db.get_value("Contract Item", poll_id, "parent")
				project_name = frappe.db.get_value(
					"Contract", child_doc.parent, "project_name")
				approver = frappe.db.get_value(
					"Project", project_name, "custom_project_lead_email")
				if approver:
					frappe.set_user(approver)
					frappe.db.set_value("Contract Item", poll_id, "sme_item", 1)

					send_ephemeral_message(
						slack_token, channel_id, user_id, ts, selected_option, slack_data.get(
							"message", {}).get("blocks", ""), block_id, poll_id
					)
					send_confirmation_message(slack_token, child_doc, approver)
					poll_message = f"Response Received for Contract - {poll_id}\n - {selected_option}"
					create_slack_log_for_poll(self=child_doc, status="Success",
                                            poll_type="Receive Response", poll_result=poll_message)

			return {"text": f"Response Recorded for '{selected_option}' recorded."}
	except Exception as e:
		create_slack_log_for_poll(self=child_doc, status="Error",
                            poll_type="Receive Response", error=str(frappe.get_traceback(e)))
		frappe.log_error("Error in slack", frappe.get_traceback(e))
