from . import __version__ as app_version

app_name = "sg_slack_integration"
app_title = "sg_slack_integration"
app_publisher = "8848 Digital"
app_description = "Slack Integration for SG"
app_email = "rohitkumar8848@digital.com"
app_license = "MIT"


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sg_slack_integration/css/sg_slack_integration.css"
# app_include_js = "/assets/sg_slack_integration/js/sg_slack_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/sg_slack_integration/css/sg_slack_integration.css"
# web_include_js = "/assets/sg_slack_integration/js/sg_slack_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sg_slack_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sg_slack_integration.utils.jinja_methods",
# 	"filters": "sg_slack_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sg_slack_integration.install.before_install"
# after_install = "sg_slack_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sg_slack_integration.uninstall.before_uninstall"
# after_uninstall = "sg_slack_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sg_slack_integration.utils.before_app_install"
# after_app_install = "sg_slack_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sg_slack_integration.utils.before_app_uninstall"
# after_app_uninstall = "sg_slack_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sg_slack_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Project": {
		"on_update": "sg_slack_integration.doc_events.project.on_update",
	},
	"Project Employee Distribution": {
		"validate": "sg_slack_integration.doc_events.ped.validate",
	},
	"Opportunity": {
		"validate": "sg_slack_integration.doc_events.opportunity.validate",
	},
    "Travel Request": {
        "on_update":"sg_slack_integration.doc_events.travel_request.on_update",
	},
    "Expense Claim": {
        "after_insert":"sg_slack_integration.doc_events.expense_claim.after_insert",
	},
	"Leave Application": {
		"on_update":"sg_slack_integration.doc_events.leave_application.on_update",
        "before_insert":"sg_slack_integration.doc_events.leave_application.before_insert"
	},
    "Compensatory Leave Request": {
		"on_update":"sg_slack_integration.doc_events.compensatory_leave_request.on_update",
        "before_insert":"sg_slack_integration.doc_events.compensatory_leave_request.before_insert"
	},
    "Project Health Assessment Survey": {
        "after_insert":"sg_slack_integration.doc_events.project_health_assessment_survey.after_insert",
    }
    # "Supplier Rating": {
    #     "after_insert":"sg_slack_integration.doc_events.supplier_rating.after_insert",
	# },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"sg_slack_integration.tasks.all"
	# ],
	"daily": [
		"sg_slack_integration.tasks.archive_opportunity_channel",
		"sg_slack_integration.doc_events.common_function.populate_slack_channel_details",
		"sg_slack_integration.doc_events.common_function.set_sharepoint_links",
	],
	# "hourly": [
	# 	"sg_slack_integration.tasks.hourly"
	# ],
	# "weekly": [
	# 	"sg_slack_integration.tasks.weekly"
	# ],
	"monthly": [
		"sg_slack_integration.doc_events.project_health_assessment_survey.create_assessment_forms"
	],
	"cron": {
		# At 9am KSA daily
		"0 9 * * *": [
			"sg_slack_integration.doc_events.slack_birthday_reminder.send_slack_birthday_greetings",
		],
	}
}

# Testing
# -------

# before_tests = "sg_slack_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sg_slack_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sg_slack_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sg_slack_integration.utils.before_request"]
# after_request = ["sg_slack_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["sg_slack_integration.utils.before_job"]
# after_job = ["sg_slack_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sg_slack_integration.auth.validate"
# ]
