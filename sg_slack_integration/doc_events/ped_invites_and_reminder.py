import frappe

from strategic_gears.strategic_gears.utils.mail import send_mail_custom
from sg_slack_integration.doc_events.project_employee_distribution import send_reminder_on_slack_to_user
# def enqueue_reminder(self):
# 	# Get the old doc from DB
# 	old_doc = frappe.get_doc(self.doctype, self.name)

# 	# Iterate over child table rows in current doc
# 	for row in self.get("distribution_detail"):
# 		# Find the matching row in old_doc (by name — child doc name is unique)
# 		old_row = next((r for r in old_doc.get("distribution_detail") if r.name == row.name), None)

# 		if old_row:
# 			if old_row.


def send_non_confirmed_mail(ped_name):
	setting = frappe.get_cached_doc("Slack Integration Settings")
	ped_doc = frappe.get_doc("Project Employee Distribution", ped_name)

	non_confirmed_emps = []

	for each_allocation in ped_doc.distribution_detail:
		if each_allocation.invite_sent == 1:
			if each_allocation.invite_accepted == 0 and (each_allocation.invite_rejected is None or each_allocation.invite_rejected == ""):
				non_confirmed_emps.append({
					"user_id": each_allocation.employee_user_id,
					"employee": each_allocation.employee,
					"employee_name": each_allocation.employee_name
					})
	

	if non_confirmed_emps:
		doc_context = frappe._dict({
			"non_confirmed_users": non_confirmed_emps,
			"ped_name": ped_doc.name,
			"proposal": ped_doc.opportunity
		})

		send_mail_custom(
			sender=setting.email_group,
			template_name="Non-Confirmed Users from PED",
			doc=doc_context,
			direct_user_group="PMO",
			ref_dt=ped_doc.doctype,
			ref_dn=ped_doc.name
		)


def ped_reminder_scheduler():
	"""
		Job to run in every 1 hour to send reminder to employees and send PMO mail. 
	"""
	slack_token = frappe.db.get_single_value("Slack Integration Settings", 'ped_token')
	now = frappe.utils.now_datetime()

	# --- 1. PMO SUMMARY ---
	ped_list = frappe.get_all(
		"Project Employee Distribution",
		filters={
			"pmo_reminder_sent": 0,
			"ped_from": "Opportunity"
		},
		fields=["name", "first_invite_sent_at"]
	)

	for ped in ped_list:
		ped_doc = frappe.get_doc("Project Employee Distribution", ped.name)

		# Check if 24 hours passed since first invite
		if frappe.utils.time_diff_in_hours(now, ped_doc.first_invite_sent_at) >= 24:
			pending_employees = [
				row for row in ped_doc.distribution_detail
				if (row.invite_sent == 1 and row.invite_accepted == 0 and (row.invite_rejected in [None, ""]))
			]
			if pending_employees:
				__send_email_to_pmo(ped_doc, pending_employees)
			frappe.db.set_value("Project Employee Distribution",ped_doc.name,"pmo_reminder_sent",1, update_modified=False)


	# --- 2. EMPLOYEE REMINDERS ---
	ped_with_pending = frappe.get_all(
		"Project Employee Distribution",
		filters={
			"ped_from": "Opportunity",
			"invite_completed": 0
			},
		fields=["name"]
	)

	for ped in ped_with_pending:
		ped_doc = frappe.get_doc("Project Employee Distribution", ped.name)

		for row in ped_doc.distribution_detail:
			if (
				row.invite_sent == 1 and row.invite_accepted==0 and (row.invite_rejected in [None,""]) and
				not row.reminder_sent and
				frappe.utils.time_diff_in_hours(now, row.invite_sent_at) >= 24
			):
				send_reminder_on_slack_to_user(row, slack_token=slack_token)
				frappe.db.set_value("Project Employee Distribution Detail", row.name, "reminder_sent",1)
		


def __send_email_to_pmo(ped_doc,pending_employees):
	setting = frappe.get_cached_doc("Slack Integration Settings")
	doc_context = frappe._dict({
			"non_confirmed_users": pending_employees,
			"ped_name": ped_doc.name,
			"proposal": ped_doc.opportunity
		})
	send_mail_custom(
			sender=setting.email_group,
			template_name="Non-Confirmed Users from PED",
			doc=doc_context,
			direct_user_group="PMO",
			ref_dt=ped_doc.doctype,
			ref_dn=ped_doc.name
		)