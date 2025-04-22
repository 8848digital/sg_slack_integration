import frappe
import json
import requests
from frappe.utils import getdate, nowdate


# from sg_slack_integration.doc_events.slack_knowledge_helper import slack_event
@frappe.whitelist(allow_guest=True)
def slack_event():
	data = json.loads(frappe.request.data)
	frappe.log_error("data", data)

	# Handle Slack URL verification
	if data.get('type') == 'url_verification':
		return data.get('challenge')

	event = data.get("event", {})
	reaction = event.get("reaction")
	channel_id = event.get("item", {}).get("channel")
	message_ts = event.get("item", {}).get("ts")
	reactor = event.get("user")  # Who reacted

	if reaction == "white_check_mark":
		# Fetch the replied message details
		message_author, thread_ts = fetch_message_author(channel_id, message_ts)

		# Fetch the parent message (thread starter)
		thread_author, _ = fetch_message_author(channel_id, thread_ts)

		# Check if the reactor is the original asker
		if reactor == thread_author:
			# ✅ Valid marking - credit the message_author (helper)
			helper_info = fetch_user_info(message_author)  # reply author info
			marker_info = fetch_user_info(reactor)         # person who marked as solved

			frappe.get_doc({
				"doctype": "Knowledge Helper Score",
				"channel_id": channel_id,
				"thread_ts": thread_ts,
				"message_ts": message_ts,
				"helper_user_id": helper_info['user_id'],
				"helper_email": helper_info['email'],
				# "helper_name": helper_info['real_name'],
				"author_user_id": marker_info['user_id'],
				"author_email": marker_info['email'],
				# "marked_by_name": marker_info['real_name'],
				"reaction": reaction,
				"date": nowdate()
			}).insert(ignore_permissions=True)
		else:
			# 🚫 Someone else reacted, ignore
			pass


def fetch_message_author(channel_id, message_ts):
	"""
	Fetches the author of a specific message in Slack (using message timestamp and channel)
	Returns: (author_user_id, thread_ts)
	"""
	slack_token = frappe.conf.get("slack_bot_token")  # Your Slack Bot Token
	if not slack_token:
		frappe.throw("Slack Bot Token not configured in site config!")

	url = "https://slack.com/api/conversations.replies"

	params = {
		"channel": channel_id,
		"ts": message_ts,
		"limit": 1  # Only one message we care about
	}

	headers = {
		"Authorization": f"Bearer {slack_token}"
	}

	response = requests.get(url, headers=headers, params=params)
	data = response.json()

	if not data.get("ok"):
		frappe.throw(f"Error fetching message: {data.get('error')}")

	messages = data.get("messages", [])

	if not messages:
		frappe.throw("No messages found for given timestamp.")

	message = messages[0]

	user_id = message.get("user")
	thread_ts = message.get("thread_ts", None) or message.get("ts")

	return user_id, thread_ts


def fetch_user_info(user_id):
	"""
	Fetch Slack user details using user_id
	Returns: {email, real_name, user_id}
	"""
	slack_token = frappe.conf.get("slack_bot_token")
	if not slack_token:
		frappe.throw("Slack Bot Token not configured in site config!")

	url = "https://slack.com/api/users.info"

	params = {
		"user": user_id
	}

	headers = {
		"Authorization": f"Bearer {slack_token}"
	}

	response = requests.get(url, headers=headers, params=params)
	data = response.json()

	if not data.get("ok"):
		frappe.throw(f"Error fetching user info: {data.get('error')}")

	user = data.get("user", {})
	email = user.get("profile", {}).get("email", "")
	real_name = user.get("real_name", "")

	return {
            "user_id": user_id,
          		"email": email,
          		"real_name": real_name
        }
