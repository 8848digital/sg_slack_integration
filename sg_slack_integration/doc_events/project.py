from sg_slack_integration.doc_events.common_function import (
    create_slack_channel, get_channel_id, set_description, set_topic)
from sg_slack_integration.doc_events.utils import compatible_slack_channel_name


def on_update(self, method=None):
    create_project_channel(self)


def create_project_channel(self):
    if not self.custom_channel_id:
        channel_name = compatible_slack_channel_name(self.project_name)
        channel_details = create_slack_channel(self, channel_name)
        if not channel_details:
            return
        project_channel_name = ""
        if channel_details["is_channel_created"] == "name_taken":
            count = 1
            while channel_details["is_channel_created"] != True:
                channel_details = create_slack_channel(self, (channel_name+"_p"+str(count)))
                count += 1
                project_channel_name = channel_details["channel_name"]
                project_channel_id = channel_details["channel_id"]

            self.custom_channel_name = project_channel_name
            self.custom_channel_id = project_channel_id

        elif channel_details["is_channel_created"]:
            self.custom_channel_name = channel_details["channel_name"]
            self.custom_channel_id = channel_details["channel_id"]
            project_channel_name = channel_name
        set_topic_and_description(self,project_channel_name)


def set_topic_and_description(self,project_channel_name):
    channel = get_channel_id(self,project_channel_name)
    if self.project_name:
        set_topic(self, channel, self.project_name)
    if self.customer:
        set_description(self, channel, self.customer + "-" + self.customer_name)
