
import frappe
import json
import requests
from sg_slack_integration.doc_events.poll_api import *
from frappe.model.workflow import apply_workflow
from frappe.core.doctype.version.version import get_diff
from strategic_gears.strategic_gears.utils.mail import get_users_from_email_group
from frappe.utils import getdate,now
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
                    try:
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
                        options = ['Yes','No']
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
                                frappe.db.set_value('Project Employee Distribution Detail',distribution_details_doc.name,'invite_sent_at',now(),update_modified=False) 
                    except Exception as e:
                        frappe.log_error(f"Sending Poll in slack {emp.get('employee')}", frappe.get_traceback(e))




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
            if poll_id and selected_option:
                distribution_details=frappe.get_doc('Project Employee Distribution Detail',poll_id)
                ped=frappe.get_doc('Project Employee Distribution',distribution_details.get('parent'))
                approver=distribution_details.get('employee_user_id')
                frappe.enqueue(
                    ped_response_store,
                    queue="long",
                    timeout=25000,
                    job_name=f"Response employee form {poll_id}",
                    poll_id=poll_id,selected_option=selected_option,slack_token=slack_token,channel_id=channel_id,user_id=user_id,ts=ts,slack_data=slack_data,block_id=block_id,
                    ped=ped,distribution_details=distribution_details,approver=approver
                )
                send_intimate_message(slack_token,distribution_details,approver)
            return {"text": f"Response Recorded for '{selected_option}' recorded."}
    except Exception as e:
        create_slack_log_for_poll(self=doc, status="Error",
		                          poll_type="Receive Response", error=str(frappe.get_traceback(e)))
        frappe.log_error("Error in slack", frappe.get_traceback(e))

def ped_response_store(poll_id,selected_option,slack_token,channel_id,user_id,ts,slack_data,block_id,approver,ped,distribution_details):
    if approver:
        frappe.set_user('Administrator')
        for ped_emp in ped.get('distribution_detail'):
            if ped_emp.get('name')==poll_id:
                if selected_option in ['Yes','No']:
                    if selected_option=='Yes':
                        ped_emp.update({'invite_accepted':1})
                        ped.save(ignore_permissions=True)
                        frappe.set_user(approver)
                        send_ephemeral_message(
                            slack_token, channel_id, user_id, ts, selected_option, slack_data.get("message", {}).get("blocks", ""), block_id, poll_id
                        )
                        send_confirmation_message(slack_token,distribution_details,approver)
                        poll_message = f"Response Received by Employee - {user_id} in {poll_id}\n - {selected_option}"
                        create_slack_log_for_poll(self=distribution_details, status="Success",
                                                            poll_type="Receive Response", poll_result=poll_message)  
                        complete_form_notification(distribution_details.get('parent'))                         
                    else:
                        resend_poll(ped_emp,slack_token)
                        
                else:
                    email_template=''
                    if selected_option:
                        ped_emp.update({'invite_rejected':selected_option})
                        ped.append('users_rejected',{'employee':distribution_details.get('employee'),'employee_name':distribution_details.get('employee_name')})
                        ped.save(ignore_permissions=True)
                        email_template = frappe.db.get_single_value(
                            "Slack Integration Settings", 'rejected_notification')
                    frappe.set_user(approver)
                    send_ephemeral_message(
                        slack_token, channel_id, user_id, ts, selected_option, slack_data.get("message", {}).get("blocks", ""), block_id, poll_id
                    )
                    send_confirmation_message(slack_token,distribution_details,approver)
                    poll_message = f"Response Received by Employee - {user_id} in {poll_id}\n - {selected_option}"
                    create_slack_log_for_poll(self=distribution_details, status="Success",
                                                        poll_type="Receive Response", poll_result=poll_message)                    
                    if email_template:
                        sending_response_mail(email_template,ped_doc=distribution_details.get('parent'),ped_child_table=distribution_details,response=selected_option)
                    complete_form_notification(distribution_details.get('parent'))


def sending_response_mail(email_template,ped_doc,ped_child_table,response):
    doc=frappe.get_doc('Project Employee Distribution',ped_doc)
    email_group = frappe.db.get_single_value(
                                    "Slack Integration Settings", 'email_group')
    if email_group:
        email_group_users=get_users_from_email_group(email_group)
        email_template_doc=frappe.get_doc('Email Template',email_template)
        subject=email_template_doc.get('subject')
        doc.update({'employee_name':ped_child_table.get('employee_name'),'from_date_employee':ped_child_table.get('from_date'),'to_date_employee':ped_child_table.get('to_date'),'rejected_reason':response})
        content = frappe.render_template(email_template_doc.response_html, {"doc": doc})
        frappe.sendmail(recipients=email_group_users,
                 subject=subject,
                 content=content,
                 reference_doctype=doc.doctype, 
                 reference_name=doc.name)

def complete_form_notification(ped):
    ped_doc=frappe.get_doc('Project Employee Distribution',ped)
    for ped_emp in ped_doc.get('distribution_detail'):
        if ped_emp.get('invite_accepted')==0 and ( not ped_emp.get('invite_rejected')):
            break
    else:
        users_list=frappe.get_all('Project Employee Distribution Details',{'parent':ped},plick="employee_user_id")
        opporunity_doc=frappe.get_doc('Opportunity',ped_doc.get('opportunity'))
        if opporunity_doc.get('custom_tech_user'):
            users_list.append(opporunity_doc.get('custom_tech_user'))
        if opporunity_doc.get('custom_partner_user'):
            users_list.append(opporunity_doc.get('custom_partner_user'))
        users_list.append(ped.get(''))

        if users_list:
            email_template = frappe.db.get_single_value(
                                    "Slack Integration Settings", 'accepted_notification')
            email_template_doc=frappe.get_doc('Email Template',email_template)
            subject=email_template_doc.get('subject')
            content = frappe.render_template(email_template_doc.response_html, {"doc": ped_doc})
            frappe.sendmail(recipients=users_list,
                    subject=subject,
                    content=content,
                    reference_doctype=ped_doc.doctype, 
                    reference_name=ped_doc.name)

@frappe.whitelist()
def send_action_reminder():
    today_date=getdate()
    PED=frappe.get_all('Project Employee Distribution',{'ped_from':'Opportunity'})
    ped_tables=frappe.get_all('Project Employee Distribution Detail',{'invite_sent':1,'invite_accepted':0,'invite_rejected':['is','not set'],'parent':['in',PED]},['*'])
    users_list=[]
    # for ped_forms in ped_tables:
    #     if getdate(ped_forms.get('creation'))!=today_date:
    #         users_list.append(ped_forms.get('employee_user_id'))
    users_list=['kanchan@8848digital.com']
    send_reminder_on_slack(users_list)

def send_reminder_on_slack(users_list):
    slack_token = frappe.db.get_single_value(
            "Slack Integration Settings", 'ped_token')
    if slack_token and len(slack_token)>0:
        response_data=[{
            "type": "header",
            "text": {"type": "plain_text", "text": "* This is a gentle reminder to take action on proposals that are pending your approval or rejection. *"}
        }]
        for email in users_list:
            user_id = get_user_id_by_email(email, slack_token)            
            if user_id:
                
                payload ={
                    "type": 'header',
                    "blocks": response_data
                }
                payload["channel"] = user_id
                payload = payload.copy()
                url = "https://slack.com/api/chat.postMessage"
                headers = {
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json",
                }
                response = requests.post(url, headers=headers, json=payload)


def send_intimate_message(slack_token,doctype,email):
    response_data=[{
		"type": "section",
		"text": {"type": "mrkdwn", "text": "* Your response is been under process! :white_check_mark: *"}
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

 

def resend_poll(ped_emp,slack_token):
    if slack_token and len(slack_token)>0:
        try:
            header_block = {
                "type": "header",
                "text": {"type": "plain_text", "text": 'Allocation in PED for Proposal- ' + ped_emp.get('parent')}
            }
            questions_and_answers = []
            questions_and_answers.append(header_block)
            sections = [
                {"title": "From Date", "content": ped_emp.get('from_date')},
                {"title":"To Date","content":ped_emp.get('to_date')},
                {"title":"Allocation %","content":ped_emp.get('ratio_')},
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
            question_text = 'Please select the reason for your unavailabilty:'
            # for val in options:
            question_block = {
                "type": "section",
                "block_id": f"question_{len(questions_and_answers) + 1}",
                "text": {"type": "mrkdwn", "text": f"*{question_text}*"}
            }
            questions_and_answers.append(question_block)
            options = ['❌Over-utilized(within system)', '❌Over-utilized(outside system)', '🏖️ On leave']
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
                "text": ped_emp.name,
                "blocks": questions_and_answers
            }
            # approver=ped_emp.get('employee_user_id')
            approver='kanchan@8848digital.com'
            user_emails = [approver]
            for email in user_emails:
                user_id = get_user_id_by_email(email, slack_token)
                if user_id:
                    payload = payload.copy()
                    payload["channel"] = user_id
                    post_poll_to_slacks(slack_token, payload,ped_emp,approver) 
        except Exception as e:
            frappe.log_error(f"Sending Poll in slack {ped_emp.get('employee')}", frappe.get_traceback(e))


