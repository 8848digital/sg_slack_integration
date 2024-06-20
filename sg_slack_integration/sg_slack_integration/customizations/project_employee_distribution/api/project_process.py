import frappe
from sg_slack_integration.sg_slack_integration.doctype.slack_integration_settings.api.common_function import (
    get_user_ids, invite_users, remove_member)


def project_process(self):
	if self.ped_from != "Project":
		return
	channel = frappe.db.get_value("Project", self.project, "custom_channel_id")
	if channel:
		self.is_channel_created = 1
		add_or_remove_users(self, channel)


def add_or_remove_users(self, channel):
    add_user_ids = get_users(self, add_or_remove_user="add")
    if add_user_ids:
        add_user_ids_str = ",".join(add_user_ids.values())
        invite_user = invite_users(self, add_user_ids_str, channel)
        if invite_user:
            for user in self.distribution_detail:
                for employee, slack_id in add_user_ids.items():
                    if user.employee == employee:
                        user.custom_is_user_added = 1

    remove_user_ids = get_users(self, add_or_remove_user="remove")
    if remove_user_ids:
        remove_member(self, remove_user_ids, channel)


def get_users(self, add_or_remove_user, method=None):
	slack_user_ids = {}
	remove_slack_user_ids = []
	if add_or_remove_user == "add":
		if self.distribution_detail:
			for user in self.distribution_detail:
				if not user.custom_is_user_added:
					email = frappe.db.get_value("Employee", user.employee, "company_email")
					if email:
						slack_user_id = get_user_ids(self, email)
						if slack_user_id:
							slack_user_ids[user.employee] = slack_user_id

	if self.ped_from == "Opportunity" and self.is_channel_created != 1:
		doc = frappe.get_doc("Opportunity", self.opportunity)
		tech_name = doc.custom_tech_name if doc.custom_tech_name else None
		proposal_manager_name = (
			doc.custom_proposal_manager_name if doc.custom_proposal_manager_name else None
		)
		partner_name = doc.custom_partner_name if doc.custom_partner_name else None
		users = frappe.db.get_list(
			"Employee",
			filters={"name": ["in", [tech_name, proposal_manager_name, partner_name]]},
			fields="company_email",
		)
		if users:
			for user in users:
				slack_user_id = get_user_ids(self, user.company_email)
				if slack_user_id:
					slack_user_ids[user.company_email] = slack_user_id

	if add_or_remove_user == "remove":
		user_list = []
		old_user_list = []
		if self.distribution_detail:
			for user in self.distribution_detail:
				user_list.append(user.employee)
			ped_exist = frappe.db.exists("Project Employee Distribution", self.name)
			if ped_exist:
				old_doc = frappe.get_cached_doc("Project Employee Distribution", self.name)
				for old_user in old_doc.distribution_detail:
					old_user_list.append(old_user.employee)
				remove_user_list = [x for x in old_user_list if x not in user_list]

				if remove_user_list:
					for user in remove_user_list:
						email = frappe.db.get_value("Employee", user, "company_email")
						slack_user_id = get_user_ids(self, email)
						if slack_user_id:
							remove_slack_user_ids.append(slack_user_id)
				return remove_slack_user_ids
	return slack_user_ids