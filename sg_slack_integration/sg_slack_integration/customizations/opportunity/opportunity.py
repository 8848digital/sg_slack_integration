from sg_slack_integration.sg_slack_integration.customizations.opportunity.doc_events.workflow import handle_workflow_state


def validate(self, method=None):
	handle_workflow_state(self)


