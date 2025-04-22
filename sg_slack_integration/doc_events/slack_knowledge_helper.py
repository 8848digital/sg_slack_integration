import frappe
import json
from frappe.utils import getdate, nowdate


# from sg_slack_integration.doc_events.slack_knowledge_helper import slack_event
@frappe.whitelist(allow_guest=True)
def slack_event():
	data = json.loads(frappe.request.data)
	frappe.log_error("data", data)
	# Handle Slack URL verification
	if data.get('type') == 'url_verification':
		return data.get('challenge')

	event = data.get('event', {})
	frappe.log_error("event", event)

	if not event:
		return "No event"

	# Only react to 'reaction_added' events
	if event.get('type') == 'reaction_added':
		reaction = event.get('reaction')
		# Only interested in 'white_check_mark' reactions
		if reaction == 'white_check_mark':
			message_id = event.get('item', {}).get('ts')
			channel_id = event.get('item', {}).get('channel')
			message_author = event.get('item_user')  # The helpful person
			reactor = event.get('user')  # The person giving the reaction
			frappe.log_error("reaction response", event)

			# Don't count self-reactions
			if message_author != reactor:
				# Check if already exists (avoid duplicates)
				if not frappe.db.exists("Knowledge Helper Score", {"message_id": message_id, "reacted_by": reactor}):
					doc = frappe.new_doc("Knowledge Helper Score")
					doc.slack_user_id = message_author
					doc.reacted_by = reactor
					doc.message_id = message_id
					doc.channel_id = channel_id
					doc.reaction = reaction
					doc.date = nowdate()
					doc.insert(ignore_permissions=True)
					frappe.db.commit()
	return "ok"
