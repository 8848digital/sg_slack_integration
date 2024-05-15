from datetime import date
from sg_slack_integration.doc_events.common_function import archive_channel
import frappe


def archive_opportunity_channel():
    opp_list = frappe.db.get_list("Opportunity", {"custom_archiving_date": str(date.today())})
    for opp_id in opp_list:
        channel_id =frappe.db.get_value("Opportunity", opp_id, "custom_channel_id")
        response = archive_channel(opp_id, channel_id)
        if response:
            frappe.db.set_value("Opportunity", opp_id, "custom_is_channel_archived", 1)
