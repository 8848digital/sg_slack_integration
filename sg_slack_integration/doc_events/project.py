import frappe
import requests
import json
from sg_slack_integration.doc_events.common_function import create_slack_channel,set_topic,set_description,get_channel_id


def validate(self, method=None):
    create_slack_channel(self)
    channel = get_channel_id(self)   
    if self.is_new():
        if self.project_name:
            set_topic(self,channel, self.project_name)
        if self.customer:
            set_description(self,channel, self.customer+"-"+self.customer_name)