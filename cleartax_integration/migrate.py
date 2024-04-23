import json
import os


def after_migrate():
	create_custom_fields()


def create_custom_fields():
	CUSTOM_FIELDS = {}
	print("Creating/Updating Custom Fields....")
	path = os.path.join(os.path.dirname(__file__), "cleartax_integration/custom_fields")
	for file in os.listdir(path):
		with open(os.path.join(path, file), "r") as f:
			# print(json.load(f))
			CUSTOM_FIELDS.update(json.load(f))
			# return f
   
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields(CUSTOM_FIELDS)
 
 
 
import json

def filter_json_data(json_data):
    field_mapping = []
    value = [0,"",None]
    for item in json_data:
        if "custom" in item["name"]:
            filtered_item = {k: v for k, v in item.items() if v not in value}
            # if item["dt"] in field_mapping.keys():
            #     field_mapping[item["dt"]] = field_mapping[item["dt"]].append(filtered_item)
            # else:
            #     field_mapping[item["dt"]] = [filtered_item]
            field_mapping.append(filtered_item)
            print(field_mapping)
    return field_mapping

with open('loan.json', 'r') as file:
    json_data = json.load(file)

filtered_json_data = filter_json_data(json_data["custom_fields"])

with open('fields.py', 'w') as file:
    json.dump(filtered_json_data, file, indent=2)