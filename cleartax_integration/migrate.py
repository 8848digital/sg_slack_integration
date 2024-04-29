import json
import os


def after_migrate():
    
	print("hello")
	create_custom_fields()

def create_custom_fields():
	CUSTOM_FIELDS = {}
	print("Creating/Updating Custom Fields....")
	path = os.path.join(os.path.dirname(__file__), "cleartax_integration/custom_field")
	for file in os.listdir(path):
		with open(os.path.join(path, file), "r") as f:
			# print(json.load(f))
			CUSTOM_FIELDS.update(json.load(f))
			# return f
   
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields(CUSTOM_FIELDS)