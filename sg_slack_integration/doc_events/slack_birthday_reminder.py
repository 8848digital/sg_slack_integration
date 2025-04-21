import frappe

import requests

from hrms.controllers.employee_reminders import get_employees_who_are_born_today


# ------------------
# BIRTHDAY REMINDERS
# ------------------
def send_slack_birthday_greetings():
	"""Send Employee birthday reminders on slack."""

	to_send = int(frappe.db.get_single_value(
		"Slack Integration Settings", "send_birthday_reminders_on_slack"))
	if not to_send:
		return

	employees_born_today = get_employees_who_are_born_today()

	for company, birthday_persons in employees_born_today.items():
		birthday_person_emails = [
			doc.get('user_id') for doc in birthday_persons]
		mentions = []
		dummy_data = frappe._dict()
		dummy_data.update({"name": "Slack Birthday Reminder"})
		for emp in birthday_person_emails:
			slack_user_id = fetch_slack_user_id_by_email(email=emp)
			if slack_user_id:
				mentions.append(f"<@{slack_user_id}>")
			else:
				mentions.append(f"@{emp}")

		message = f"🎉 Happy Birthday to {' , '.join(mentions)}! 🎂 Let's celebrate! 🎊"
		send_to_slack(message)


def fetch_slack_user_id_by_email(email):
	bot_token = frappe.db.get_single_value(
		"Slack Integration Settings", "bday_bot_token")
	url = "https://slack.com/api/users.lookupByEmail"
	headers = {
		"Authorization": f"Bearer {bot_token}"
	}
	params = {
		"email": email
	}
	response = requests.get(url, headers=headers, params=params)
	data = response.json()
	if data.get("ok"):
		return data["user"]["id"]
	else:
		frappe.log_error(f"Slack Lookup Error: {data.get('error')}")
		return None


def send_to_slack(text):
	bot_token = frappe.db.get_single_value(
		"Slack Integration Settings", "bday_bot_token")
	channel_id = frappe.db.get_single_value(
		"Slack Integration Settings", "channel_id")

	payload = {
		"channel": channel_id,
		"text": text,
	}

	headers = {
		"Authorization": f"Bearer {bot_token}",
		"Content-Type": "application/json"
	}

	response = requests.post(
		"https://slack.com/api/chat.postMessage", json=payload, headers=headers)

	if not response.ok or not response.json().get('ok'):
		frappe.log_error(f"Slack API Error: {response.text}")
		return

	resp_json = response.json()
	# 🎯 If message was sent successfully, add a reaction
	ts = resp_json.get("ts")
	if ts:
		add_reaction_to_message(channel_id, ts, "tada", bot_token)


def add_reaction_to_message(channel, ts, emoji_name, bot_token):
    url = "https://slack.com/api/reactions.add"
    payload = {
        "channel": channel,
        "timestamp": ts,
        "name": emoji_name  # Emoji without colons
    }

    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }

    reaction_response = requests.post(url, json=payload, headers=headers)
    reaction_json = reaction_response.json()

    if not reaction_response.ok or not reaction_json.get('ok'):
        frappe.log_error(f"Slack Reaction Error: {reaction_response.text}")
