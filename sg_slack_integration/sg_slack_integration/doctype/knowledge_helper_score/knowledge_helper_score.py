# Copyright (c) 2025, 8848 Digital and contributors
# For license information, please see license.txt

# from sg_slack_integration.sg_slack_integration.doctype.knowledge_helper_score.knowledge_helper_score import slack_event
import frappe
from frappe.model.document import Document
import json
import requests
from frappe.utils import getdate, nowdate

class KnowledgeHelperScore(Document):
	pass




@frappe.whitelist(allow_guest=True)
def slack_event():
	settings = frappe.get_cached_doc("Slack Integration Settings")
	if not settings.enable_scoring:
		frappe.log_error("Knowledge Helper Scoring",
		                 "Scoring not Enabled in Slack Integration Settings")
		return
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
	main_message_ts = ""

	if channel_id == settings.channel_id_to_calculate_the_score_from:
		if reaction == settings.score_based_on_emoji_reaction:
			# Fetch the replied message details
			message_author, thread_ts = fetch_message_author(channel_id, message_ts)

			# Fetch the parent message (thread starter)
			thread_author, main_message_ts = fetch_message_author(channel_id, thread_ts)

			# Check if the reactor is the original asker
			# if reactor == thread_author:
			# 	# ✅ Valid marking - credit the message_author (helper)

			# reply author info
			helper_info = fetch_user_info(message_author)
			# query owner
			thread_author_info = fetch_user_info(thread_author)
			# person who marked as solved
			reactor_info = fetch_user_info(reactor)

			if not frappe.db.exists("Knowledge Helper Score", {"main_message_ts": main_message_ts, "author_email_id": thread_author_info['email']}):
				frappe.get_doc({
					"doctype": "Knowledge Helper Score",
					"channel_id": channel_id,
					"thread_ts": thread_ts,
					"message_ts": message_ts,
					"helper_user_id": helper_info['user_id'],
					"helper_email": helper_info['email'],
					# "helper_name": helper_info['real_name'],
					"author_user_id": thread_author_info['user_id'],
					"author_email": thread_author_info['email'],
					"verified_by_user_id": reactor_info['user_id'],
					"verified_by_email": reactor_info['email'],
					# "marked_by_name": marker_info['real_name'],
					"reaction": reaction,
					"date": nowdate()
				}).insert(ignore_permissions=True)
			# else:
			# 	# 🚫 Someone else reacted, ignore
			# 	pass


def fetch_message_author(channel_id, message_ts):
	"""
	Fetches the author of a specific message in Slack (using message timestamp and channel)
	Returns: (author_user_id, thread_ts)
	"""
	# slack_token = frappe.conf.get("slack_bot_token")  # Your Slack Bot Token
	slack_token = frappe.db.get_single_value(
		"Slack Integration Settings", "bday_bot_token")
	if not slack_token:
		frappe.throw("Slack Bot Token not configured in Slack Integration Settings!")

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
		frappe.log_error("Knowledge Helper Score | fetch_message_author",
		                 f"Error fetching message: {data.get('error')}")

	messages = data.get("messages", [])

	if not messages:
		frappe.log_error("Knowledge Helper Score | fetch_message_author",
		                 "No messages found for given timestamp.")

	message = messages[0]

	user_id = message.get("user")
	thread_ts = message.get("thread_ts", None) or message.get("ts")

	return user_id, thread_ts


def fetch_user_info(user_id):
	"""
	Fetch Slack user details using user_id
	Returns: {email, real_name, user_id}
	"""
	slack_token = frappe.db.get_single_value(
		"Slack Integration Settings", "bday_bot_token")

	# slack_token = frappe.conf.get("slack_bot_token")
	if not slack_token:
		frappe.throw("Slack Bot Token not configured in Slack Integration Settings!")

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
		frappe.log_error("Knowledge Helper Score | fetch_user_info",
		                 f"Error fetching user info: {data.get('error')}")

	user = data.get("user", {})
	email = user.get("profile", {}).get("email", "")
	real_name = user.get("real_name", "")

	return {
            "user_id": user_id,
          		"email": email,
          		"real_name": real_name
        }
