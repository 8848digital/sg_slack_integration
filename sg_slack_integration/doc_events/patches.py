import re
import requests
import frappe

def get_list_of_ped():
    result_list = []

    list = frappe.db.get_list("Project Employee Distribution",
                            {"ped_from": "Opportunity", "is_channel_created" : "1"})
    print(len(list))
    count = 0
    for ped in list:
        opportunity_id = frappe.db.get_value("Project Employee Distribution",
                                            ped["name"], "opportunity", as_dict=True)
        channel_name = frappe.db.get_value("Opportunity", opportunity_id["opportunity"],
                                        "custom_channel_name", as_dict=True)
        channel_id = frappe.db.get_value("Opportunity", opportunity_id["opportunity"],
                                        "custom_channel_id", as_dict=True)
        # channel_id = get_channel_id(channel_name["custom_channel_name"])
        # frappe.db.set_value('Opportunity',opportunity_id["opportunity"],
        #                         "custom_channel_id",channel_id, update_modified=False)
        # Create a dictionary containing the data along with channel_id
        data_with_channel_id = {
            "ped_name": ped["name"],
            "opportunity_id": opportunity_id["opportunity"],
            "channel_name": channel_name["custom_channel_name"],
            "channel_id": channel_id["custom_channel_id"]
        }

        result_list.append(data_with_channel_id)
        # print(data_with_channel_id)
        count += 1
        print (count)

    print (result_list)
    return "result_list"


def get_list_of_project():
    result_list = []

    list = [{'name': 'PROJ-1011'}, {'name': 'PROJ-1010'}, {'name': 'PROJ-1003'}, {'name': 'PROJ-1007'}, {'name': 'PROJ-1004'}, {'name': 'PROJ-1009'}, {'name': 'PROJ-1006'}, {'name': 'PROJ-1005'}]
    print(list)
    for project in list:

        channel_name = frappe.db.get_value("Project", project["name"],
                                        "custom_channel_name", as_dict=True)
        channel_id = frappe.db.get_value("Project", project["name"],
                                        "custom_channel_id", as_dict=True)
        if channel_id == None:
            return project

        data_with_channel_id = {
            "project_id": project["name"],
            "channel_name": channel_name["custom_channel_name"],
            "channel_id": channel_id["custom_channel_id"]
        }
        result_list.append(data_with_channel_id)

    print(result_list)

    return len(list)


def set_opportunity_channel_details():
    list_of_ped = []
    for ped in list_of_ped:
        if frappe.db.exists("Project Employee Distribution", ped["ped_name"]):
             frappe.db.set_value("Project Employee Distribution", ped["ped_name"], "is_channel_created", 1, update_modified=False)

        if frappe.db.exists("Opportunity", ped["opportunity_id"]):
            frappe.db.set_value("Opportunity", ped["opportunity_id"],  {"custom_channel_name": ped["channel_name"],
                                                                    "custom_channel_id": ped["channel_id"]}, update_modified=False)
        else:
            print (ped)


def set_project_channel_details():
    list_of_projects = []

    for project in list_of_projects:
        if frappe.db.exists("Project", project["project_id"]):
            frappe.db.set_value("Project", project["project_id"],  {"custom_channel_name": project["channel_name"],
                                                                    "custom_channel_id": project["channel_id"]}, update_modified=False)
        else:
            print (project)


def create_project_channel_by_saving_doc():
    list = frappe.db.get_list("Project", {"custom_channel_id": ["is","not set"]})
    print (list)
    return "Done"
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
        except Exception as e:
            error_list.append({"name":i["name"], "custom_channel_name":doc.custom_channel_name})
            print (error_list)
            frappe.logger("project_logs").exception(error_list)
    print (error_list)
    return "DONE"


def set_member():
    a = frappe.db.get_value("Project Employee Distribution Detail", {"parent": "PED-27758", "employee":"SG-592"}, "name")
    frappe.db.set_value("Project Employee Distribution Detail", a, "is_user_added" ,0 )
    frappe.db.set_value("Project Employee Distribution", "PED-27758", "is_channel_created" ,0 )



def list_of_new_ped():
    list = frappe.db.get_list("Project Employee Distribution",
                            {"ped_from": "Opportunity", "is_channel_created" : "1"})
    print(len(list))
    count = 0
    result_list = []
    for ped in list:
        opportunity_id = frappe.db.get_value("Project Employee Distribution",
                                            ped["name"], "opportunity", as_dict=True)
        channel_id = frappe.db.get_value("Opportunity", opportunity_id["opportunity"],
                                        "custom_channel_id", as_dict=True)
        if channel_id["custom_channel_id"] == None:
            data_with_channel_id = {
                "ped_name": ped["name"],
                "opportunity_id": opportunity_id["opportunity"]
            }

            result_list.append(data_with_channel_id)
    print(result_list)
    print(len(result_list))


def get_list_of_new_ped():
    result_list = []
    a = []
    list = [{'ped_name': 'PED-27918', 'opportunity_id': 'CRM-OPP-2024-01029'}, {'ped_name': 'PED-27916', 'opportunity_id': 'CRM-OPP-2024-01028'}, {'ped_name': 'PED-27913', 'opportunity_id': 'CRM-OPP-2024-01106'}, {'ped_name': 'PED-27915', 'opportunity_id': 'CRM-OPP-2024-00991'}, {'ped_name': 'PED-27914', 'opportunity_id': 'CRM-OPP-2024-00908'}, {'ped_name': 'PED-27907', 'opportunity_id': 'CRM-OPP-2024-00918'}, {'ped_name': 'PED-27908', 'opportunity_id': 'CRM-OPP-2024-00805'}, {'ped_name': 'PED-27906', 'opportunity_id': 'CRM-OPP-2024-00803'}, {'ped_name': 'PED-27905', 'opportunity_id': 'CRM-OPP-2024-01108'}, {'ped_name': 'PED-27897', 'opportunity_id': 'CRM-OPP-2024-01001'}, {'ped_name': 'PED-27869', 'opportunity_id': 'CRM-OPP-2024-00937'}, {'ped_name': 'PED-27895', 'opportunity_id': 'CRM-OPP-2024-01105'}, {'ped_name': 'PED-27856', 'opportunity_id': 'CRM-OPP-2024-01000'}, {'ped_name': 'PED-27868', 'opportunity_id': 'CRM-OPP-2024-00909'}, {'ped_name': 'PED-27867', 'opportunity_id': 'CRM-OPP-2024-01031'}, {'ped_name': 'PED-27864', 'opportunity_id': 'CRM-OPP-2024-01030'}, {'ped_name': 'PED-27866', 'opportunity_id': 'CRM-OPP-2024-00990'}, {'ped_name': 'PED-27841', 'opportunity_id': 'CRM-OPP-2024-00719'}, {'ped_name': 'PED-27789', 'opportunity_id': 'CRM-OPP-2024-00904'}, {'ped_name': 'PED-27790', 'opportunity_id': 'CRM-OPP-2024-00903'}, {'ped_name': 'PED-27780', 'opportunity_id': 'CRM-OPP-2024-00789'}, {'ped_name': 'PED-27855', 'opportunity_id': 'CRM-OPP-2024-00992'}, {'ped_name': 'PED-27838', 'opportunity_id': 'CRM-OPP-2024-00969'}, {'ped_name': 'PED-27788', 'opportunity_id': 'CRM-OPP-2024-00833'}, {'ped_name': 'PED-27847', 'opportunity_id': 'CRM-OPP-2024-00920'}, {'ped_name': 'PED-27840', 'opportunity_id': 'CRM-OPP-2024-00733'}, {'ped_name': 'PED-27842', 'opportunity_id': 'CRM-OPP-2024-00905'}, {'ped_name': 'PED-27839', 'opportunity_id': 'CRM-OPP-2024-00767'}, {'ped_name': 'PED-27818', 'opportunity_id': 'CRM-OPP-2024-00774'}, {'ped_name': 'PED-27710', 'opportunity_id': 'CRM-OPP-2024-00770'}, {'ped_name': 'PED-27816', 'opportunity_id': 'CRM-OPP-2024-00907'}, {'ped_name': 'PED-27779', 'opportunity_id': 'CRM-OPP-2024-00779'}, {'ped_name': 'PED-27723', 'opportunity_id': 'CRM-OPP-2024-00784'}, {'ped_name': 'PED-27824', 'opportunity_id': 'CRM-OPP-2024-00782'}, {'ped_name': 'PED-27817', 'opportunity_id': 'CRM-OPP-2024-00775'}, {'ped_name': 'PED-27823', 'opportunity_id': 'CRM-OPP-2024-00832'}, {'ped_name': 'PED-27815', 'opportunity_id': 'CRM-OPP-2024-00804'}, {'ped_name': 'PED-27786', 'opportunity_id': 'CRM-OPP-2024-00812'}, {'ped_name': 'PED-27778', 'opportunity_id': 'CRM-OPP-2024-00809'}, {'ped_name': 'PED-27797', 'opportunity_id': 'CRM-OPP-2024-00769'}, {'ped_name': 'PED-27787', 'opportunity_id': 'CRM-OPP-2024-00921'}, {'ped_name': 'PED-27791', 'opportunity_id': 'CRM-OPP-2024-00906'}, {'ped_name': 'PED-27792', 'opportunity_id': 'CRM-OPP-2024-00913'}, {'ped_name': 'PED-27720', 'opportunity_id': 'CRM-OPP-2024-00632'}, {'ped_name': 'PED-27781', 'opportunity_id': 'CRM-OPP-2024-00734'}, {'ped_name': 'PED-27770', 'opportunity_id': 'CRM-OPP-2024-00780'}, {'ped_name': 'PED-27725', 'opportunity_id': 'CRM-OPP-2024-00811'}, {'ped_name': 'PED-27773', 'opportunity_id': 'CRM-OPP-2024-00729'}, {'ped_name': 'PED-27772', 'opportunity_id': 'CRM-OPP-2024-00730'}, {'ped_name': 'PED-27771', 'opportunity_id': 'CRM-OPP-2024-00790'}, {'ped_name': 'PED-27769', 'opportunity_id': 'CRM-OPP-2024-00838'}, {'ped_name': 'PED-27752', 'opportunity_id': 'CRM-OPP-2024-00806'}, {'ped_name': 'PED-27751', 'opportunity_id': 'CRM-OPP-2024-00837'}, {'ped_name': 'PED-27711', 'opportunity_id': 'CRM-OPP-2024-00807'}, {'ped_name': 'PED-27724', 'opportunity_id': 'CRM-OPP-2024-00710'}, {'ped_name': 'PED-27722', 'opportunity_id': 'CRM-OPP-2024-00562'}, {'ped_name': 'PED-27709', 'opportunity_id': 'CRM-OPP-2024-00810'}, {'ped_name': 'PED-27649', 'opportunity_id': 'CRM-OPP-2024-00714'}, {'ped_name': 'PED-27617', 'opportunity_id': 'CRM-OPP-2024-00679'}, {'ped_name': 'PED-13113', 'opportunity_id': 'CRM-OPP-2023-00514'}]
    print(len(list))
    count = 0
    for ped in list:
        channel_id = frappe.db.get_value("Opportunity", ped["opportunity_id"],
                                        "proposal_name", as_dict=True)
        channel_name = channel_id["proposal_name"].lower().replace(" ", "_")
        channel_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", channel_name)[:80]
        channel_id = get_channel_id(channel_name)
        if channel_id == None:
            a.append(ped["opportunity_id"])
        frappe.db.set_value('Opportunity',ped["opportunity_id"],
                                {"custom_channel_name": channel_name,
                                    "custom_channel_id": channel_id}, update_modified=False)
        # Create a dictionary containing the data along with channel_id
        data_with_channel_id = {
            "ped_name": ped["ped_name"],
            "opportunity_id": ped["opportunity_id"],
            "channel_name": channel_name,
            "channel_id": channel_id
        }

        # Append the dictionary to the result list
        result_list.append(data_with_channel_id)
        print(data_with_channel_id)
        count += 1
        print (count)
    print(a)
    print (result_list)
    return "result_list"


def get_channel_id(channel_name):
    token = frappe.db.get_single_value("Token", "token")
    if token:
        url = "https://slack.com/api/conversations.list"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {"limit": 999, "types": "public_channel, private_channel"}
        cursor = None
        while True:
            if cursor:
                payload["cursor"] = cursor

            response = requests.request("POST", url, headers=headers, data=payload)
            res = response.json()


            if res["ok"]:
                    for channel in res["channels"]:
                        if channel.get("name") == channel_name:
                            return channel.get("id")

                    if not res["response_metadata"]["next_cursor"]:
                        break

                    cursor = res["response_metadata"]["next_cursor"]