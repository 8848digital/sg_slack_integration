import frappe

from sg_slack_integration.doc_events.common_function import (
    create_slack_channel, get_channel_id, set_description, set_topic)


def validate(self, method=None):
	if self.is_new():
		create_slack_channel(self)
		set_topic_and_description(self)


def set_topic_and_description(self):
	channel = get_channel_id(self)
	if self.is_new():
		if self.project_name:
			set_topic(self, channel, self.project_name)
		if self.customer:
			set_description(self, channel, self.customer + "-" + self.customer_name)
