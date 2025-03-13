import frappe
from sg_slack_integration.doc_events.poll_api import *
import json

def after_insert(doc,method):
    print('kkkk')
    post_poll_supplier_rating(doc.name)


def post_poll_supplier_rating(doc_name):
    doc=frappe.get_doc('Supplier Rating',doc_name)
    approver=doc.get('evaluator')
    poll_enabled=frappe.db.get_single_value("Slack Integration Settings", 'enable_poll')
    options = ['1', '2', '3', '4', '5']
    if poll_enabled:
        slack_token=frappe.db.get_single_value('Slack Integration Settings','supplier_rating_token')
        if slack_token and len(slack_token)>0:
            header_block = {
                "type": "header",
                "text": {"type": "plain_text", "text": 'Supplier Evaluation'}
            }
            questions_and_answers = []
            questions_and_answers.append(header_block)
            sections = [
                {"title": "Supplier", "content": doc.supplier_name},
                {"title": "Purchase Order", "content": doc.reference_purchase_order},
                {"title":'Purchase Order Reference','content':frappe.utils.get_url_to_form('Purchase Order', doc.reference_purchase_order)},
                {"title":'Supplier Reference','content':frappe.utils.get_url_to_form('Supplier', doc.supplier_id)},
                {"title":'Form Reference','content':frappe.utils.get_url_to_form(doc.doctype, doc.name)}
            ]
            for section in sections:
                description_block = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{section['title']}*: *{section['content']}*"  if section.get('title') not in ['Form Reference','Supplier Reference','Purchase Order Reference'] else f"*{section['title']}*: {section['content']}"
                    },
                }
                questions_and_answers.append(description_block)
            question_text = 'Your Action on Supplier Rating'
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
                    post_poll_to_slacks(slack_token, payload,doc,approver)



@frappe.whitelist(allow_guest=True)
def handle_poll_response():
    try:
        slack_token = frappe.db.get_single_value(
			"Slack Integration Settings", 'supplier_rating_token')
        payload = frappe.request.form.get("payload")
        frappe.log_error('Slack- Supplier Response',payload)
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
            doc=frappe.get_doc('Supplier Rating',poll_id)
            approver=doc.get('evaluator')
            if approver:
                frappe.set_user(approver)
                doc.rating=int(selected_option)/5
                doc.save(ignore_permissions=True)
                doc.submit()
                send_ephemeral_message(
                    slack_token, channel_id, user_id, ts, selected_option, slack_data.get("message", {}).get("blocks", ""), block_id, poll_id
                )
                send_confirmation_message(slack_token,doc,approver)
                poll_message = f"Response Received for Employee - {user_id} in {poll_id}\n - {selected_option}"
                create_slack_log_for_poll(self=doc, status="Success",
							                          poll_type="Receive Response", poll_result=poll_message)

        return {"text": f"Response Recorded for '{selected_option}' recorded."}
    except Exception as e:
        create_slack_log_for_poll(self=doc, status="Error",
		                          poll_type="Receive Response", error=str(frappe.get_traceback(e)))
        frappe.log_error("Error in slack Supplier Rating", frappe.get_traceback(e))