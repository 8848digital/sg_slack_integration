import frappe
from sg_slack_integration.doc_events.common_function import (
    create_slack_channel,
    get_channel_id,
    set_topic,
    set_description,
    send_file,
    invite_users,
    get_user_ids,
    remove_member,
)


def validate(self, method=None):
    opportunity_process(self)
    project_process(self)
            
            
def opportunity_process(self):
    if self.ped_from != "Opportunity":
        return 
    user_ids = get_users(self)
    
    topic_and_description = frappe.get_value("Opportunity",self.opportunity,
                                                ['title', 'name', 'expected_closing'], as_dict=1)

    channel = get_channel_id(self)
    
    if self.is_channel_created == 0:
        is_channel_exists = create_slack_channel(self)
        channel = get_channel_id(self)
        if is_channel_exists == True or is_channel_exists == "name_taken":
            self.is_channel_created = 1
    
        if is_channel_exists != "name_taken":
            topic = f"{topic_and_description.title}-{topic_and_description.name}"
            description = f"Expected closing Date: {str(topic_and_description.expected_closing)}"
            set_topic(self, channel, topic)
            set_description(self, channel, description)
            send_file(self, channel)
        
    if channel:
        if user_ids:
            invite_users(user_ids, channel)
            removed_user_slack_ids = removed_user_slack_id(self,user_ids)
            if removed_user_slack_ids:
                remove_member(removed_user_slack_ids, channel)


def project_process(self):
    if self.ped_from == "Project":
        user_ids = get_users(self)
        channel = get_channel_id(self)
        if channel: 
            if user_ids:
                invite_users(user_ids, channel)
                removed_user_slack_ids = removed_user_slack_id(self,user_ids)
                if removed_user_slack_ids:
                    remove_member(removed_user_slack_ids, channel)


def get_users(self,method=None):
    slack_user_ids = ""
    if self.distribution_detail:
        for user in self.distribution_detail:
            email = frappe.db.get_value("Employee",user.employee,'company_email')
            if email:
                slack_user_id = get_user_ids(email)
                if slack_user_id:
                    slack_user_ids += slack_user_id+","
    if self.ped_from == "Opportunity":
        doc = frappe.get_doc("Opportunity",self.opportunity)
        tech_name = doc.custom_tech_name if doc.custom_tech_name else None
        proposal_manager_name = doc.custom_proposal_manager_name if doc.custom_proposal_manager_name else None
        partner_name = doc.custom_partner_name if doc.custom_partner_name else None
        users = frappe.db.get_list("Employee", 
                                   filters = {'name' : ["in", [tech_name, proposal_manager_name, partner_name]]},
                                   fields = 'company_email')
        if users:
            for user in users:
                slack_user_id = get_user_ids(user.company_email)
                if slack_user_id:
                    slack_user_ids += slack_user_id+","
    return slack_user_ids


def removed_user_slack_id(self, user_ids):
    present_user_ids = []
    remove_slack_user_ids = []
    
    ped_exist = frappe.db.exists("Project Employee Distribution", self.name)
    
    if ped_exist:
        old_doc = frappe.get_cached_doc("Project Employee Distribution", self.name)
        for user in old_doc.distribution_detail:
            email_to_remove = frappe.db.get_value("Employee",user.employee,'company_email')
            if email_to_remove:
                present_user_id = get_user_ids(email_to_remove)
                if present_user_id:
                    present_user_ids.append(present_user_id)
                    
    user_id_set = set(user_ids.split(','))
    present_user_id_set = set(present_user_ids)
    
    for remove_slack_user_id in present_user_id_set:
        if remove_slack_user_id not in user_id_set:
            remove_slack_user_ids.append(remove_slack_user_id)
            
    return remove_slack_user_ids