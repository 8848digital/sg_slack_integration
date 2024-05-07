import json

from sg_slack_integration.doc_events.utils import compatible_slack_channel_name, create_slack_log
import frappe
import requests
from frappe import _


def create_slack_channel(self, channel_name, method=None):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")
	if token:
		url = "https://slack.com/api/conversations.create"
		headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}

		data = json.dumps({"name": channel_name, "is_private": "true"})
	try:
		response = requests.post(url, data=data, headers=headers)
		res = response.json()
		if res["ok"]:
			success_msg = "Channel created successfully"
			frappe.msgprint(_(success_msg))
			create_slack_log(self, success_msg, error=None)
			return {"is_channel_created" : res["ok"],
					"channel_name":channel_name,
					"channel_id":res["channel"]["id"]
					}

		elif not res["ok"] and res["error"] == "name_taken":
			return {"is_channel_created" : res["error"],
					"channel_name":channel_name,
					"channel_id":None
					}

		elif not res["ok"]:
			error_msg = "Channel creation failed"
			email_context = {
				"record_name": self.name,
				"error": error_msg,
				"response": res,
			}
			create_slack_log(self, error_msg, error=str(res))
			log_error_context = {"record_name": self.name, "channel_name": channel_name, "error": error_msg}
			send_mail(email_context)
			frappe.msgprint(_(error_msg))
			frappe.log_error(error_msg, log_error_context)
		else:
			frappe.throw(_("Please set Slack Token First"))
	except Exception as e:
		frappe.throw(_("An error occurred while creating channel: " + str(e)))


def set_topic(self, channel, topic):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")
	if token:
		url = "https://slack.com/api/conversations.setTopic"
		headers = {
			"Content-Type": "application/json; charset=utf-8",
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
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")

	if token:
		url = "https://slack.com/api/conversations.setPurpose"
		headers = {
			"Content-Type": "application/json; charset=utf-8",
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


def archive_channel(opp_id, channel):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")

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
				return res["ok"]
			elif not res["ok"] and res["error"] != "already_archived":
				error = "Channel archiving failed for {0}".format(opp_id)
				email_context = {"record_name": opp_id, "error": error, "response": res}
				log_error_context = {"record_name": opp_id, "error": error}
				send_mail(email_context)
				frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.log_error("An error occurred:", str(e))
	else:
		frappe.msgprint(_("Please set Slack Token First"))


def unarchive_channel(self, channel):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")

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
				return res["ok"]
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
		token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")
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


def get_user_ids(self, email):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")
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
			# email_context = {"record_name": self.name, "error": error, "response": res}
			log_error_context = {"record_name": self.name, "error": error}
			# send_mail(email_context)
			# frappe.msgprint(_(error))
			frappe.log_error(error, log_error_context)


def invite_users(self, user_ids, channel):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")
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
				return res["ok"]
			elif not res["ok"] and res["error"] == "already_in_channel":
				return True
			else:
				error = "User invitation failed"
				# email_context = {"record_name": self.name, "error": error, "response": res}
				log_error_context = {"record_name": self.name, "error": error}
				# send_mail(email_context)
				# frappe.msgprint(_(error))
				frappe.log_error(error, log_error_context)
		except Exception as e:
			frappe.throw(_("There is an error trying to invite users"))
	else:
		frappe.throw(_("Please set Slack Token First"))


def remove_member(self, user_ids_to_remove, channel_id):
	token = frappe.db.get_single_value("Slack Integration Settings", "slack_token")

	url = "https://slack.com/api/conversations.kick"
	headers = {
		"Content-Type": "application/x-www-form-urlencoded",
		"Authorization": "Bearer {0}".format(token),
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
	settings_doc = frappe.get_doc("Slack Integration Settings").as_dict()
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
