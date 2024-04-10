import json
import re

import frappe
import requests
from frappe import _

def create_slack_channel(self, method=None):
	token = frappe.db.get_single_value("Token", "token")
	if token:
		url = "https://slack.com/api/conversations.create"
		headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

		if self.doctype == "Project":
			name = self.project_name.lower().replace(" ", "_")
		if self.doctype == "Project Employee Distribution":
			name = frappe.get_value("Opportunity", self.opportunity, "proposal_name")
			name = name.lower().replace(" ", "_")

		name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", name)[:80]
		data = json.dumps({"name": name, "is_private": "true"})
	try:
		response = requests.post(url, data=data, headers=headers)
		res = response.json()
		if res["ok"]:
			frappe.msgprint(_("Channel created successfully on Slack"))
			return res["ok"]
		elif not res["ok"] and res["error"] == "name_taken":
			frappe.msgprint(_("Channel Already exists"))
			return res["error"]
		elif not res["ok"]:
			error = "Channel creation for {0} failed".format(self.name)
			email_context = {
				"record_name": self.name,
				"error": error,
				"response": res,
			}
			log_error_context = {"record_name": self.name, "channel_name": name, "error": error}
			send_mail(email_context)
			frappe.msgprint(_(error))
			frappe.log_error(error, log_error_context)
		else:
			frappe.throw(_("Please set Slack Token First"))
	except Exception as e:
		frappe.throw(_("An error occurred while creating channel: " + str(e)))


def get_channel_id(self, method=None):
	if self.doctype == "Opportunity":
		channel_name = self.proposal_name.lower().replace(" ", "_")
	elif self.doctype == "Project":
		channel_name = self.project_name.lower().replace(" ", "_")
	elif self.doctype == "Project Employee Distribution":
		if self.ped_from == "Opportunity":
			channel_name = frappe.get_value("Opportunity", self.opportunity, "proposal_name")
		if self.ped_from == "Project":
			channel_name = frappe.get_value("Project", self.project, "project_name")

	channel_name = channel_name.lower().replace(" ", "_")
	channel_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", channel_name)[:80]

	token = frappe.db.get_single_value("Token", "token")

	if token:
		url = "https://slack.com/api/conversations.list"
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/x-www-form-urlencoded",
		}
		payload = {"limit": 999, "types": "public_channel, private_channel"}
		try:
			response = requests.request("POST", url, headers=headers, data=payload)
			res = response.json()
			if res["ok"]:
				for channel in res["channels"]:
					if channel.get("name") == channel_name:
						return channel.get("id")
			else:
				error = f"Channel ID for {self.name} not found"
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.log_error("An error occurred while setting topic:", str(e))
	else:
		frappe.throw(_("Please set Slack Token First"))


def set_topic(self, channel, topic):
	token = frappe.db.get_single_value("Token", "token")
	if token:
		url = "https://slack.com/api/conversations.setTopic"
		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {token}",
		}
		payload = {
			"channel": channel,
			"topic": topic,
		}
		try:
			response = requests.post(url, headers=headers, json=payload)
			res = response.json()
			if res["ok"]:
				frappe.msgprint(_("Topic set successfully on Slack"))
			else:
				error = "Topic set unsuccessful"
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)

		except Exception as e:
			frappe.log_error("An error occurred while setting topic:", str(e))
	else:
		frappe.msgprint(_("Please set Slack Token First"))


def set_description(self, channel, description):
	token = frappe.db.get_single_value("Token", "token")

	if token:
		url = "https://slack.com/api/conversations.setPurpose"
		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {token}",
		}
		payload = {
			"channel": channel,
			"purpose": description,
		}
		try:
			response = requests.post(url, headers=headers, json=payload)
			res = response.json()
			if res["ok"]:
				frappe.msgprint(_("Description set successfully on Slack"))
			else:
				error = "Description set Failed"
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)

		except Exception as e:
			frappe.log_error("An error occurred while setting description:", str(e))
	else:
		frappe.msgprint(_("Please set Slack Token First"))


def archive_channel(self, channel):
	token = frappe.db.get_single_value("Token", "token")

	if token:
		url = "https://slack.com/api/conversations.archive"
		headers = {
			"Content-Type": "application/json; charset=utf-8",
			"Authorization": f"Bearer {token}",
		}
		payload = {
			"channel": channel,
		}
		try:
			response = requests.post(url, headers=headers, json=payload)
			res = response.json()
			if res["ok"]:
				frappe.msgprint(_("Channel Archived Successfully"))
			else:
				error = "Channel archiving failed for {0}".format(self.name)
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.log_error("An error occurred:", str(e))
	else:
		frappe.msgprint(_("Please set Slack Token First"))


def unarchive_channel(self, channel):
	token = frappe.db.get_single_value("Token", "token")

	if token:
		url = "https://slack.com/api/conversations.unarchive"
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json; charset=utf-8",
		}
		payload = {
			"channel": channel,
		}
		try:
			response = requests.post(url, headers=headers, json=payload)
			res = response.json()
			if res["ok"]:
				frappe.msgprint(_("Channel Unarchived Successfully"))
			else:
				error = "Channel unarchiveing failed for {0}".format(self.name)
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.log_error("An error occurred:", str(e))
	else:
		frappe.msgprint(_("Please set Slack Token First"))


def send_file(self, channel):
	files = frappe.db.get_list(
		"File",
		filters={"attached_to_name": self.opportunity, "attached_to_doctype": "Opportunity"},
		fields=["name"],
	)
	for file in files:
		token = frappe.db.get_single_value("Token", "token")
		if token:
			url = "https://slack.com/api/files.upload"
			headers = {"Authorization": f"Bearer {token}"}
			data = {"channels": channel, "initial_comment": "Here is RFP file!"}
			file = frappe.utils.file_manager.get_file(file.name)
			files = {
				"file": (file),
			}
			try:
				response = requests.post(url, data=data, files=files, headers=headers)
				res = response.json()
				if res["ok"]:
					frappe.msgprint(_("File sent successfully on Slack"))
				else:
					error = "File send unsuccessfully"
					email_context = {"record_name": self.name, "error": error, "response": res}
					log_error_context = {"record_name": self.name, "error": error}
					send_mail(email_context)
					frappe.msgprint(_(error))
					frappe.log_error(error, log_error_context)
			except Exception as e:
				frappe.log_error("An error occurred:", str(e))
		else:
			frappe.msgprint(_("Please set SLack Token First"))


def invite_users(self, user_ids, channel):
	token = frappe.db.get_single_value("Token", "token")
	if token:
		url = "https://slack.com/api/conversations.invite"
		headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
		data = json.dumps({"users": user_ids, "channel": channel, "forced": True})
		try:
			response = requests.request(
				"POST",
				url,
				data=data,
				headers=headers,
			)
			res = response.json()
			if res["ok"]:
				frappe.msgprint(_("Users invited successfully"))
			else:
				error = "User invitation failed"
				email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.throw(_("There is an error trying to invite users"))
	else:
		frappe.throw(_("Please set Slack Token First"))


def get_user_ids(self, email):
	token = frappe.db.get_single_value("Token", "token")
	if token:
		url = "https://slack.com/api/users.lookupByEmail"
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/x-www-form-urlencoded",
		}
		data = f"email={email}"
		response = requests.request("POST", url, data=data, headers=headers)
		res = response.json()
		if res["ok"]:
			return res["user"].get("id")
		else:
			error = "Slack User {0} not found".format(email)
			email_context = {"record_name": self.name, "error": error, "response": res}
			log_error_context = {"record_name": self.name, "error": error}
			send_mail(email_context)
			frappe.msgprint(_(error))
			frappe.log_error(error, log_error_context)


def remove_member(self, user_ids_to_remove, channel_id):
	token = frappe.db.get_single_value("Token", "token")

	url = f"https://slack.com/api/conversations.kick"
	headers = {
		"Content-Type": "application/x-www-form-urlencoded",
		"Authorization": f"Bearer {token}",
	}
	for user_id_to_remove in user_ids_to_remove:
		data = {"channel": channel_id, "user": user_id_to_remove}
		response = requests.post(url, headers=headers, params=data)
		res = response.json()
		if response.ok:
			frappe.msgprint(_("User removed from channel"))
		else:
			error = "Error removing user from channel"
			email_context = {"record_name": self.name, "error": error, "response": res}
			log_error_context = {"record_name": self.name, "error": error}
			send_mail(email_context)
			frappe.msgprint(_(error))
			frappe.log_error(error, log_error_context)


def send_mail(context):
	settings_doc = frappe.get_doc("Slack Error Notification").as_dict()
	recipient = settings_doc.get("slack_error_notification_email")
	recipient_emails = [user["user"] for user in recipient]
	template_name = settings_doc.get("slack_error_notification_template")

	try:
		frappe.sendmail(
			recipients=recipient_emails,
			subject=frappe.render_template(
				frappe.db.get_value("Email Template", template_name, "subject"),
				context,
			),
			cc="",
			bcc="",
			delayed=False,
			message=frappe.render_template(
				frappe.db.get_value("Email Template", template_name, "response"),
				context,
			),
			reference_doctype="",
			reference_name="",
			attachments="",
			print_letterhead=False,
		)
	except Exception as e:
		frappe.log_error("Slack Email Error", e)
