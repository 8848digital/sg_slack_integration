from sg_slack_integration.sg_slack_integration.customizations.project_employee_distribution.api.opportunity_process import opportunity_process
from sg_slack_integration.sg_slack_integration.customizations.project_employee_distribution.api.project_process import project_process


def validate(self, method=None):
	opportunity_process(self)
	project_process(self)

