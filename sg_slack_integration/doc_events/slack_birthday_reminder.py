import frappe

import requests


from frappe.utils import today


# ------------------
# BIRTHDAY REMINDERS
# ------------------
def send_slack_birthday_greetings():
	"""Send Employee birthday reminders on slack."""

	to_send = int(frappe.db.get_single_value(
		"Slack Integration Settings", "send_birthday_reminders_on_slack"))
	if not to_send:
		return

	employees_born_today = get_employees_having_an_event_today("birthday")

	for company, birthday_persons in employees_born_today.items():
		birthday_person_emails = [
			doc.get('user_id') for doc in birthday_persons]
		mentions = []
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

	site_verified = False
	site_url = frappe.db.get_single_value(
		"Strategic Gears HR Settings", "site_url") or None
	if site_url:
		if site_url == frappe.utils.get_url():
			site_verified = True

	if site_verified:
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
		frappe.log_error(f"Send Slack Birthday Reminder",
                   f"{frappe.utils.get_url()} -> {str(frappe.utils.now_datetime())}")

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


def get_employees_having_an_event_today(event_type):
	"""Get all employee who have `event_type` today
	& group them based on their company. `event_type`
	can be `birthday` or `work_anniversary`"""

	from collections import defaultdict
	from frappe.utils import today


	# Set column based on event type
	if event_type == "birthday":
		condition_column = "date_of_birth"
	elif event_type == "work_anniversary":
		condition_column = "date_of_joining"
	else:
		return

	employees_born_today = frappe.db.multisql(
		{
			"mariadb": f"""
			SELECT `personal_email`, `company`, `company_email`, `user_id`, `employee_name` AS 'name', `image`, `date_of_joining`
			FROM `tabEmployee`
			WHERE
				DAY({condition_column}) = DAY(%(today)s)
			AND
				MONTH({condition_column}) = MONTH(%(today)s)
			AND
				YEAR({condition_column}) < YEAR(%(today)s)
			AND
				`status` in ('Active','Leaving')
		""",
			"postgres": f"""
			SELECT "personal_email", "company", "company_email", "user_id", "employee_name" AS 'name', "image"
			FROM "tabEmployee"
			WHERE
				DATE_PART('day', {condition_column}) = date_part('day', %(today)s)
			AND
				DATE_PART('month', {condition_column}) = date_part('month', %(today)s)
			AND
				DATE_PART('year', {condition_column}) < date_part('year', %(today)s)
			AND
				"status" in ('Active','Leaving')
		""",
		},
		dict(today=today(), condition_column=condition_column),
		as_dict=1,
	)

	grouped_employees = defaultdict(lambda: [])

	for employee_doc in employees_born_today:
		grouped_employees[employee_doc.get("company")].append(employee_doc)

	return grouped_employees
