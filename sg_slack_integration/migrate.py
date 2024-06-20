import json
import os
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_migrate():
	"""
	# NOTE: No custom field or property yet in this app yet.
	create_custom_fields()
	create_property_setter()
	"""
	pass



def create_custom_fields():
	CUSTOM_FIELDS = {}
	print("Creating/Updating Custom Fields....")
	path = os.path.join(os.path.dirname(__file__), "sg_slack_integration/custom_fields")
	for file in os.listdir(path):
		with open(os.path.join(path, file), "r") as f:
			CUSTOM_FIELDS.update(json.load(f))
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(CUSTOM_FIELDS)


def create_property_setter():
	print("Creating/Updating Property Setters....")
	path = os.path.join(os.path.dirname(__file__), "sg_slack_integration/property_setters")
	for file in os.listdir(path):
		with open(os.path.join(path, file), "r") as f:
			property_setters = json.load(f)
			for doctype, properties in property_setters.items():
				for args in properties:
					if not args.get("doctype"):
						args["doctype"] = doctype
					make_property_setter(**args)