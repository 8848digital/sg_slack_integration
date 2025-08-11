import frappe

from sg_slack_integration.doc_events.common_function import (
    create_slack_channel, get_user_ids, invite_users,
    remove_member, send_file, set_description, set_topic)
from sg_slack_integration.doc_events.utils import compatible_slack_channel_name


def validate(self, method=None):
	lead_process(self)
	opportunity_process(self)
	project_process(self)


def opportunity_process(self):
    if self.ped_from != "Opportunity":
        return

    opportunity_details = get_opportunity_details(self)

    if self.is_channel_created == 0:
        channel_details = create_or_get_slack_channel(self, opportunity_details)
        if not channel_details:
            return
        if channel_details["is_channel_created"] == True:
            self.is_channel_created = 1
            set_opportunity_channel_values(self, channel_details)
            set_channel_properties(self, opportunity_details)

    manage_channel_members(self)


def lead_process(self):
	if self.ped_from != "Lead":
		return
	lead_details = get_lead_details(self)
	if self.is_channel_created == 0:
		channel_details = create_or_get_slack_channel(self, lead_details)
		if not channel_details:
			return
		if channel_details["is_channel_created"] == True:
			self.is_channel_created = 1
			set_lead_channel_values(self, channel_details)
			set_channel_properties_lead(self, lead_details)

	manage_channel_members_lead(self)


def project_process(self):
	if self.ped_from != "Project":
		return
	channel = frappe.db.get_value("Project", self.project, "custom_channel_id")
	if channel:
		self.is_channel_created = 1
		add_or_remove_users(self, channel)


def get_opportunity_details(self):
    return frappe.get_value(
        "Opportunity", self.opportunity, ["proposal_name", "title", "name", "expected_closing", "custom_sharepoint_link"], as_dict=1
    )


def get_lead_details(self):
	lead_detail = frappe.get_value(
		"Lead", self.lead, ["custom_client_name", "title", "name", "custom_expected_contract_date", "custom_sharepoint_link"], as_dict=1
	)
	lead_detail.update({
		"proposal_name": lead_detail.custom_client_name
	})
	return lead_detail


def create_or_get_slack_channel(self, opportunity_details):
    channel_name = compatible_slack_channel_name(opportunity_details.proposal_name)
    channel_details = create_slack_channel(self, channel_name)
    if not channel_details:
        return
    if channel_details["is_channel_created"] == "name_taken":
        count = 1
        while channel_details["is_channel_created"] != True:
            channel_details = create_slack_channel(self, (channel_name+"_"+str(count)))
            count += 1
    return channel_details


def set_opportunity_channel_values(self, channel_details):
    frappe.db.set_value("Opportunity", self.opportunity,
                        {"custom_channel_name": channel_details["channel_name"],
                         "custom_channel_id": channel_details["channel_id"]})


def set_lead_channel_values(self, channel_details):
    frappe.db.set_value("Lead", self.lead,
                        {"custom_channel_name": channel_details["channel_name"],
                         "custom_channel_id": channel_details["channel_id"]})


def set_channel_properties(self, opportunity_details):
	channel = frappe.db.get_value(
		"Opportunity", self.opportunity, "custom_channel_id")
	if channel:
		topic = f"{opportunity_details.title}-{opportunity_details.name}"
		description = (
			f"Expected closing Date: {str(opportunity_details.expected_closing)}"
		)
		if opportunity_details.get("custom_sharepoint_link") != "" or opportunity_details.get("custom_sharepoint_link") is not None:
			description = f"SharePoint Link --> {opportunity_details.get('custom_sharepoint_link')}"
		set_topic(self, channel, topic)
		set_description(self, channel, description)
		send_file(self, channel)


def set_channel_properties_lead(self, lead_details):
	channel = frappe.db.get_value("Lead", self.lead, "custom_channel_id")
	if channel:
		topic = f"{lead_details.title}-{lead_details.name}"
		description = (
			f"Expected Contract Date: {str(lead_details.custom_expected_contract_date)}"
		)
		if lead_details.get("custom_sharepoint_link") != "" or lead_details.get("custom_sharepoint_link") is not None:
			description = f"SharePoint Link --> {lead_details.get('custom_sharepoint_link')}"
		set_topic(self, channel, topic)
		set_description(self, channel, description)
		send_file(self, channel)


def manage_channel_members(self):
    channel = frappe.db.get_value("Opportunity", self.opportunity, "custom_channel_id")
    if channel:
        add_or_remove_users(self, channel)


def manage_channel_members_lead(self):
    channel = frappe.db.get_value("Lead", self.lead, "custom_channel_id")
    if channel:
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
	is_proposal_ped = True if self.ped_from == "Opportunity" else False
	if add_or_remove_user == "add":
		if self.distribution_detail:
			for user in self.distribution_detail:
				proceed_to_add = True
				if is_proposal_ped and user.invite_accepted != 1:
					proceed_to_add = False
				if proceed_to_add:
					if not user.custom_is_user_added:
						email = frappe.db.get_value("Employee", user.employee, "company_email")
						if email:
							slack_user_id = get_user_ids(self, email)
							if slack_user_id:
								slack_user_ids[user.employee] = slack_user_id

	if self.ped_from == "Opportunity":
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

	if self.ped_from == "Lead":
		doc = frappe.get_doc("Lead", self.lead)
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
