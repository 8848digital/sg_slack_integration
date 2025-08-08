
import frappe
import json
import requests
from sg_slack_integration.doc_events.poll_api import *
from frappe.model.workflow import apply_workflow
from frappe.core.doctype.version.version import get_diff

def after_insert(self,method):
    if self.ped_from=='Opportunity':
        employee_details=self.distribution_detail
        doc_name=self.name
        doc=self
        post_poll_ped(employee_details,doc_name,doc)
    

def on_update(self,method):
    if self.ped_from=='Opportunity':
        doc_to_compare = self._doc_before_save
        employee_details=[]
        if doc_to_compare:
            current_doc_changes = get_diff(doc_to_compare, self)
            if current_doc_changes:
                employee_details=self.distribution_detail
                doc_name=self.name
                doc=self
                post_poll_ped(employee_details,doc_name,doc)

     

def post_poll_ped(employee_details,doc_name,doc):
    slack_token = frappe.db.get_single_value(
            "Slack Integration Settings", 'ped_token')
    if slack_token and len(slack_token)>0:
        opportunity_doc=frappe.get_doc('Opportunity',doc.get('opportunity'))
        if employee_details:
            for emp in employee_details:
                if emp.get('invite_sent')!=1:
                    distribution_details_doc=frappe.get_doc('Project Employee Distribution Detail',emp.get('name'))
                    header_block = {
                        "type": "header",
                        "text": {"type": "plain_text", "text": 'New Allocation in PED for Proposal- ' + doc_name}
                    }
                    questions_and_answers = []
                    questions_and_answers.append(header_block)
                    sections = [
                        {"title": "From Date", "content": emp.get('from_date')},
                        {"title":"To Date","content":emp.get('to_date')},
                        {"title":"Allocation %","content":emp.get('ratio_')},
                        {"title":"Proposal Name","content":opportunity_doc.get('proposal_name')},
                    ]

                    for section in sections:
                        description_block = {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{section['title']}*: *{section['content']}*"
                            },
                        }
                        questions_and_answers.append(description_block)
                    question_text = 'Are you available to work on this proposal?'
                    # for val in options:
                    question_block = {
                        "type": "section",
                        "block_id": f"question_{len(questions_and_answers) + 1}",
                        "text": {"type": "mrkdwn", "text": f"*{question_text}*"}
                    }
                    questions_and_answers.append(question_block)
                    options = ['Yes',
                                '❌Over-utilized(within system)', '❌Over-utilized(outside system)', '🏖️ On leave']
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
                        "text": distribution_details_doc.name,
                        "blocks": questions_and_answers
                    }
                    # approver=emp.get('employee_user_id')
                    approver='kanchan@8848digital.com'
                    user_emails = [approver]
                    for email in user_emails:
                        user_id = get_user_id_by_email(email, slack_token)
                        if user_id:
                            payload = payload.copy()
                            payload["channel"] = user_id
                            post_poll_to_slacks(slack_token, payload,distribution_details_doc,approver) 
                            frappe.db.set_value('Project Employee Distribution Detail',distribution_details_doc.name,'invite_sent',1,update_modified=False)       





@frappe.whitelist(allow_guest=True)
def handle_poll_response():
    try:
        doc='Project Employee Distribution Detail'
        slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'ped_token')
        if slack_token:
            payload = frappe.request.form.get("payload")
            if not payload:
                frappe.log_error("error in format")
                return {"error": "Invalid payload format."}
        
            slack_data = json.loads(payload)
            frappe.log_error('slack_data Data',slack_data)
            user_id = slack_data.get("user", {}).get("username")
            channel_id = slack_data.get("channel", {}).get("id")
            action = slack_data.get("actions", [])[0]
            block_id = action.get("block_id", "")
            poll_id = slack_data.get("message", {}).get("text", "")
            selected_option = action.get("value")
            # get_mail = get_slack_user_details( slack_data.get("user", {}).get("id"), slack_token)
            ts = slack_data.get("message",{}).get("ts", "")
            complete_data=[user_id,channel_id,action,block_id,poll_id,selected_option,ts]
            frappe.log_error('Response Data',complete_data)
            if poll_id and selected_option:
                distribution_details=frappe.get_doc('Project Employee Distribution Detail',poll_id)
                ped=frappe.get_doc('Project Employee Distribution',distribution_details.get('parent'))
                approver=distribution_details.get('employee_user_id')
                if approver:
                    frappe.set_user(approver)
                    for ped_emp in ped.get('distribution_detail'):
                        if ped_emp.get('name')==poll_id:
                            if selected_option=='Yes':
                                ped_emp.update({'invite_accepted':1})
                            else:
                                ped_emp.update({'invite_rejected':selected_option})
                                ped.append('users_rejected',{'employee':distribution_details.get('employee'),'employee_name':distribution_details.get('employee_name')})
                            ped.save(ignore_permissions=True)
                        send_ephemeral_message(
                            slack_token, channel_id, user_id, ts, selected_option, slack_data.get("message", {}).get("blocks", ""), block_id, poll_id
                        )
                        send_confirmation_message(slack_token,distribution_details,approver)
                        poll_message = f"Response Received by Employee - {user_id} in {poll_id}\n - {selected_option}"
                        create_slack_log_for_poll(self=distribution_details, status="Success",
                                                            poll_type="Receive Response", poll_result=poll_message)

            return {"text": f"Response Recorded for '{selected_option}' recorded."}
    except Exception as e:
        create_slack_log_for_poll(self=doc, status="Error",
		                          poll_type="Receive Response", error=str(frappe.get_traceback(e)))
        frappe.log_error("Error in slack", frappe.get_traceback(e))

