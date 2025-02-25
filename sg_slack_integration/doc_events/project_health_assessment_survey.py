
import frappe
import json
import requests
from sg_slack_integration.doc_events.poll_api import *
from frappe.model.workflow import apply_workflow
from frappe.utils import getdate
def after_insert(self,method):
    post_poll_health_assessment(self.name)


def post_poll_health_assessment(doc_name):
    doc=frappe.get_doc('Project Health Assessment Survey',doc_name)
    approver=frappe.db.get_value('Employee', doc.employee_id, 'user_id')
    # approver='kanchan@8848digital.com'
    poll_enabled = frappe.db.get_single_value(
			"Slack Integration Settings", 'enable_poll')
    if poll_enabled:
        slack_token = frappe.db.get_single_value(
                "Slack Integration Settings", 'project_health_assessment_survey_token')
        if slack_token and len(slack_token)>0: 
            header_block = {
                "type": "header",
                "text": {"type": "plain_text", "text": 'Project Health Assessment'}
            }
            questions_and_answers = []
            questions_and_answers.append(header_block)
            sections = [
                {"title": "Project", "content": doc.project},
                {"title": "Project Name", "content": doc.project_name},
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
            meta = frappe.get_meta(doc.doctype)  # Get metadata of the DocType
            rating_fields = {df.fieldname: df.label for df in meta.fields if df.fieldtype == "Rating"}
            count=1
            for val in rating_fields:
                question_text = rating_fields[val]
                options = ['1', '2', '3', '4', '5']

                # Add question block
                question_block = {
                    "type": "section",
                    "block_id": f"question_{val}",
                    "text": {"type": "mrkdwn", "text": f"*{count}. {question_text}*"}
                }
                questions_and_answers.append(question_block)

                # Add answer block
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
                    "block_id": f"answer_{val}",
                    "elements": answer_elements
                }
                questions_and_answers.append(answer_block)
                count+=1
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
                    post_poll_to_slacks(slack_token, payload,doc,approver)
				


@frappe.whitelist(allow_guest=True)
def handle_poll_response():
    try:
        slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'project_health_assessment_survey_token')
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

        if poll_id and selected_option and 'answers_' in block_id:
            doc=frappe.get_doc('Project Health Assessment Survey',poll_id)
            approver=frappe.db.get_value('Employee', doc.employee_id, 'user_id')
            if approver:
                frappe.set_user(approver)
                # apply_workflow(doc,selected_option)
                answer_field=block_id.split('answer_')[1].strip()
                # doc[answer_field]=selected_option
                doc.update({answer_field:selected_option})
                doc.save()
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


def create_assessment_forms():
    doc=frappe.get_all('Employee',{'status':['in',['Active','Leaving']],"department": ['in', ["Shared Pool - SG","Consulting - SG"]]},['name','employee_name','user_id','current_project','department'])
    for i in doc:
        try:
            if i.get('user_id'):
                if not frappe.db.exists('Project Health Assessment Survey',{'month':getdate().month,'year':getdate().year,'employee_id':i.get('name')}):
                    if i.get('current_project'):
                        doc = frappe.new_doc("Project Health Assessment Survey")
                        doc.employee_id = i.get('name')
                        doc.employee_name = i.get('employee_name')
                        doc.project = i.get('current_project')
                        doc.project_name = frappe.db.get_value("Project",i.get('current_project'),"project_name")
                        doc.month=getdate().month
                        doc.year=getdate().year
                        doc.flags.ignore_mandatory = True
                        doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error('Form Creation-Project Health Assessment Survey',e)