import json
import re

import requests
import frappe


def project_list():
    list = frappe.db.get_list("Project", {"custom_channel_id": ["is","not set"],
                                      "project_manager": ["is","not set"]})
    # # print(list)
    print(len(list))
    error_list = []
    count = 0
    for i in list:
        doc = frappe.get_doc("Project", i["name"])
        try:
            doc.save()
            frappe.db.commit()
            count+=1
            print(count)
            print(i["name"])
            # return i
        except Exception as e:
            error_list.append({"name":i["name"], "custom_channel_name":doc.custom_channel_name})
            print (error_list)
            frappe.logger("project_logs").exception(error_list)
    print (error_list)
    return "DONE"