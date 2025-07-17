
import frappe
import json
from sg_slack_integration.doc_events.leave_application import handle_poll_response as handle_poll_response_leave_application
from sg_slack_integration.doc_events.compensatory_leave_request import handle_poll_response as handle_poll_response_compensatory_leave_application
from sg_slack_integration.doc_events.travel_request import handle_poll_response as handle_poll_response_travel_request
from sg_slack_integration.doc_events.expense_claim import handle_poll_response as handle_poll_response_expense_claim
from sg_slack_integration.doc_events.sme_contract import handle_poll_response as handle_poll_response_sme_contract
from sg_slack_integration.doc_events.employee_profile import handle_poll_response as handle_poll_response_employee_profile



@frappe.whitelist(allow_guest=True)
def handle_slack_response_erp():
    try:
        payload = frappe.request.form.get("payload")
        if not payload:
            frappe.log_error("error in format")
            return {"error": "Invalid payload format."}

        slack_data = json.loads(payload)
        poll_id = slack_data.get("message", {}).get("text", "")
        blocks=slack_data.get("message", {}).get("blocks", "")
        if poll_id:
            for block in blocks:
                if block.get('type')=='header':
                    doc_ref=block.get('text',{}).get('text','')
                    if 'Travel Request' in doc_ref:
                        handle_poll_response_travel_request(slack_data)
                    elif 'Expense Claim' in doc_ref:
                        handle_poll_response_expense_claim(slack_data)
                    elif 'Leave Application' in doc_ref:
                        handle_poll_response_leave_application(slack_data)
                    elif 'Compensatory Leave Request' in doc_ref:
                        handle_poll_response_compensatory_leave_application(slack_data)
                    elif 'SME Contract' in doc_ref:
                        handle_poll_response_sme_contract(slack_data)
                    elif doc_ref.startswith('Hi'):
                        handle_poll_response_employee_profile(slack_data)
                

    except Exception as e:
        frappe.log_error('Handle Erp Notification',e)
