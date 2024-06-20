import frappe
from sg_slack_integration.sg_slack_integration.customizations.project.api.create_channel import create_project_channel

def on_update(self, method=None):
    create_project_channel(self)


