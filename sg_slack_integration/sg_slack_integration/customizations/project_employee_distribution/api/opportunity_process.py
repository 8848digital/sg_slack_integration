import frappe

from sg_slack_integration.sg_slack_integration.doctype.slack_integration_settings.api.common_function import (
    create_slack_channel,send_file, set_description, set_topic)
from sg_slack_integration.sg_slack_integration.doctype.slack_integration_settings.api.utils import compatible_slack_channel_name
from sg_slack_integration.sg_slack_integration.customizations.project_employee_distribution.api.project_process import add_or_remove_users


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

def get_opportunity_details(self):
    return frappe.get_value(
        "Opportunity", self.opportunity, ["proposal_name", "title", "name", "expected_closing"], as_dict=1
    )

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


def set_channel_properties(self, opportunity_details):
    channel = frappe.db.get_value("Opportunity", self.opportunity, "custom_channel_id")
    if channel:
        topic = f"{opportunity_details.title}-{opportunity_details.name}"
        description = (
            f"Expected closing Date: {str(opportunity_details.expected_closing)}"
        )
        set_topic(self, channel, topic)
        set_description(self, channel, description)
        send_file(self, channel)

def manage_channel_members(self):
    channel = frappe.db.get_value("Opportunity", self.opportunity, "custom_channel_id")
    if channel:
        add_or_remove_users(self, channel)