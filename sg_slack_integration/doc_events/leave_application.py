
import frappe
import json
import requests
from sg_slack_integration.doc_events.poll_api import *
from frappe.model.workflow import apply_workflow

def on_update(self,method):
    doc_val=frappe.get_doc(self.doctype,self.name)
    old_doc = self.get_doc_before_save()
    frappe.db.set_value(doc_val.doctype,doc_val.name,'custom_initial_call',1,update_modified=False)
    if old_doc and doc_val.custom_initial_call==0:
        actions=['Approve','Reject']
        approver=''
        project = frappe.db.get_value("Employee", self.employee, "current_project")
        if old_doc.workflow_state == "Draft" and self.workflow_state == "Awaiting Line Manager Approval":
            approver=self.custom_line_manager
        elif old_doc.workflow_state == "Draft" and self.workflow_state == "Awaiting Partner Approval":
            if project:
                project_partner = frappe.db.get_value("Project", project, "project_lead")
                approver=frappe.db.get_value("Employee", project_partner, "user_id")
        elif old_doc.workflow_state == "Draft" and self.workflow_state == "Awaiting Project Manager Approval":
            approver=self.project_manager
        
        if approver and len(approver)>0:
            post_poll_leave_application(approver,actions,self.name)


        
                

def post_poll_leave_application(approver,options,doc_name):
    # approver='kanchan@8848digital.com'
    doc=frappe.get_doc('Leave Application',doc_name)
    poll_enabled = frappe.db.get_single_value(
			"Slack Integration Settings", 'enable_poll')
    if poll_enabled:
        slack_token = frappe.db.get_single_value(
                "Slack Integration Settings", 'leave_application_token')
        if slack_token and len(slack_token)>0:
            header_block = {
                "type": "header",
                "text": {"type": "plain_text", "text": 'Leave Application Request By- ' + doc.employee_name}
            }
            questions_and_answers = []
            questions_and_answers.append(header_block)
            sections = [
                {"title": "Employee Name", "content": doc.employee_name},
                {"title": "From Date", "content": doc.from_date},
                {"title":"To Date","content":doc.to_date},
                {"title":"Leave Type","content":doc.leave_type},
                {"title":"Total Leave Days","content":doc.total_leave_days},
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
            question_text = 'Your Action on Employee Request'
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
            for email in user_emails:
                user_id = get_user_id_by_email(email, slack_token)
                if user_id:
                    payload = payload.copy()
                    payload["channel"] = user_id
                    print(approver)
                    post_poll_to_slacks(slack_token, payload,doc,approver)
			
        



@frappe.whitelist(allow_guest=True)
def handle_poll_response():
    try:
        slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'leave_application_token')
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
        ts = slack_data.get("message",{}).get("ts", "")

        if poll_id and selected_option:
            doc=frappe.get_doc('Leave Application',poll_id)
            approver=''
            project = frappe.db.get_value("Employee", doc.employee, "current_project")
            if doc.workflow_state == "Awaiting Line Manager Approval":
                approver=doc.custom_line_manager
            elif doc.workflow_state == "Awaiting Partner Approval":
                if project:
                    project_partner = frappe.db.get_value("Project", project, "project_lead")
                    approver=frappe.db.get_value("Employee", project_partner, "user_id")
            elif doc.workflow_state == "Awaiting Project Manager Approval":
                approver=doc.project_manager
            if approver:
                frappe.set_user(approver)
                apply_workflow(doc,selected_option)
                send_ephemeral_message(
                    slack_token, channel_id, user_id, ts, selected_option, slack_data.get("message", {}).get("blocks", ""), block_id, poll_id
                )
                poll_message = f"Response Received for Employee - {user_id} in {poll_id}\n - {selected_option}"
                create_slack_log_for_poll(self=doc, status="Success",
							                          poll_type="Receive Response", poll_result=poll_message)

        return {"text": f"Response Recorded for '{selected_option}' recorded."}
    except Exception as e:
        create_slack_log_for_poll(self=doc, status="Error",
		                          poll_type="Receive Response", error=str(frappe.get_traceback(e)))
        frappe.log_error("Error in slack", frappe.get_traceback(e))


def before_insert(self,method):
    self.custom_initial_call=0