import frappe
import json
# import requests
from frappe.model.workflow import apply_workflow

from sg_slack_integration.doc_events.poll_api import *


def after_insert(self, method=None):
	if self.party_type == 'Supplier':
		# old_doc = self.get_doc_before_save()
		# if old_doc:
		# 	if old_doc.worflow_state != self.workflow_state and self.workflow_state == "Approved By Project Lead":
		if self.custom_project_name:
			approver = frappe.db.get_value(
				"Project", self.custom_project_name, "custom_project_lead_email")
			if approver:
				options = ["Approve", "Reject"]
				post_sme_contract_partner_approval(
					approver=approver, options=options, doc_name=self.name)
			else:
				frappe.log_error(
					f"Slack Poll - Contract {self.name}", "Partner Email not found in Project", "Contract", self.name)
		else:
			frappe.log_error(
				f"Slack Poll - Contract {self.name}", "Project Name not found in Contract", "Contract", self.name)


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
                    "style": "primary"
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
            user_emails = ['saffaat@8848digital.com']
            for email in user_emails:
                user_id = get_user_id_by_email(email, slack_token)
                if user_id:
                    payload = payload.copy()
                    payload["channel"] = user_id
                    post_poll_to_slacks(slack_token, payload, doc, approver)


@frappe.whitelist(allow_guest=True)
def handle_poll_response():
    try:
        slack_token = frappe.db.get_single_value(
            "Slack Integration Settings", 'sme_contract_token')
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

        if poll_id and selected_option:
            doc = frappe.get_doc('Contract', poll_id)
            approver = ''
            project_name = frappe.db.get_value(
                "Contract", poll_id, "custom_project_name")
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
    except Exception as e:
        create_slack_log_for_poll(self=doc, status="Error",
                                  poll_type="Receive Response", error=str(frappe.get_traceback(e)))
        frappe.log_error("Error in slack", frappe.get_traceback(e))


@frappe.whitelist()
def send_poll_on_slack_for_approve(docname, project):
    #   child_doc = frappe.get_doc("Contract Item", docname)
    approver = frappe.db.get_value(
    	"Project", project, "custom_project_lead_email")
    options = ["Approve", "Reject"]
    post_item_approval_on_slack(approver, options, docname)


def post_item_approval_on_slack(approver, options, doc_name):
    doc = frappe.get_doc('Contract Item', doc_name)
    poll_enabled = frappe.db.get_single_value(
        "Slack Integration Settings", 'enable_poll')
    if poll_enabled:
        slack_token = frappe.db.get_single_value(
            "Slack Integration Settings", 'sme_contract_token')
        if slack_token and len(slack_token) > 0:
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
                {"title": "Item Name", "content": doc.custom_project_name},
                {"title": "Currency", "content": doc.custom_currency},
                {"title": "Description", "content": doc.description},
                {"title": "Qty", "content": doc.qty},
                {"title": "Rate", "content": doc.rate},
                {"title": "Rate", "content": doc.total},
                {"title": 'Form Reference', 'content': frappe.utils.get_url_to_form(
                	"Contract", doc.parent)},
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
                    "style": "primary"
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
                "text": "item_"+doc.name,
                "blocks": questions_and_answers
            }
            user_emails = [approver]
            for email in user_emails:
                user_id = get_user_id_by_email(email, slack_token)
                if user_id:
                    payload = payload.copy()
                    payload["channel"] = user_id
                    post_poll_to_slacks(slack_token, payload, doc, approver)


@frappe.whitelist(allow_guest=True)
def handle_poll_response_item():
	try:
		slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'sme_contract_token')
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
				child_doc = frappe.get_doc('Contract Item', poll_id)
				parent_contract = frappe.db.get_value("Contract Item", poll_id, "parent")
				project_name = frappe.db.get_value(
					"Contract", parent_contract, "project_name")
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
