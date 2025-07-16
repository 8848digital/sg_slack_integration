
import frappe
import json
from sg_slack_integration.doc_events.leave_application import handle_poll_response as handle_poll_response_leave_application
from sg_slack_integration.doc_events.compensatory_leave_request import handle_poll_response as handle_poll_response_compensatory_leave_application
from sg_slack_integration.doc_events.travel_request import handle_poll_response as handle_poll_response_travel_request
from sg_slack_integration.doc_events.expense_claim import handle_poll_response as handle_poll_response_expense_claim



@frappe.whitelist(allow_guest=True)
def handle_slack_response_erp():
    try:
        payload = frappe.request.form.get("payload")
        if not payload:
            frappe.log_error("error in format")
            return {"error": "Invalid payload format."}

        slack_data = json.loads(payload)
        poll_id = slack_data.get("message", {}).get("text", "")
        if poll_id:
            if poll_id.startswith('HR-LAP-'):
                handle_poll_response_leave_application(slack_data)
            elif poll_id.startswith('HR-CMP-'):
                handle_poll_response_compensatory_leave_application(slack_data)
            elif '-TPR=' in poll_id:
                handle_poll_response_travel_request(slack_data)
            elif poll_id.startswith('HR-EXP-'):
                handle_poll_response_expense_claim(slack_data)
    except Exception as e:
        frappe.log_error('Handle Erp Notification',e)
