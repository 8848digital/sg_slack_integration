import requests
import frappe

@frappe.whitelist(allow_guest= True)
def create_opp_channel():

    doc = frappe.db.get_all("Project Employee Distribution", filters={'ped_from': 'Opportunity', "is_channel_created":0}, as_list=True)
    print(len(doc))
    count = 0
    for i in doc:
        count += 1
        print (count)
        print (i[0])
        if count ==3:
                return
        opp = frappe.db.get_value("Project Employee Distribution", i[0], "opportunity")
        # if i[0] not in ["PED-26629","PED-27176","PED-27174","PED-26646","PED-26632","PED-26612","PED-26613","PED-26592",
        #                 "PED-26337","PED-26609","PED-26610"]:
        if frappe.db.get_value("Opportunity", opp, "workflow_state") !="workflow_state":
            doc1 = frappe.get_doc("Project Employee Distribution", i[0])
            # if doc1.have_data_correct == 0:
            #     doc1.have_data_correct = 1
            # if doc1.have_data_correct == 1:
            #     doc1.have_data_correct = 0
            doc1.save(ignore_permissions=True)

            # return doc1
@frappe.whitelist(allow_guest= True)
def check_channel():
    count = 0
    docs = frappe.get_list("Project Employee Distribution", {"ped_from":"Opportunity", "is_channel_created":0})
    print(len(docs))
    print(docs)
    allocation = []
    list_of_cancelled = []
    for i in docs:
        count+=1
        print(count)
        doc1 = frappe.get_doc("Project Employee Distribution", i.get("name"))
        workflow = frappe.db.get_value("Opportunity", doc1.opportunity, "workflow_state")
        print(workflow)
        if workflow != "Cancelled":
            try:
                print(i.get("name"))
                # doc1.flags.ignore_validate = True
                doc1.save(ignore_permissions=True)
                # return
            except Exception as e:
                allocation.append(i.get("name"))
                print(e)
        else:
            list_of_cancelled.append(i.get("name"))
    print ("list_of_cancelled", len(list_of_cancelled))
    print ("allocation", len(allocation))
    print (allocation)
    print (list_of_cancelled)
    # return list_of_cancelled


def get_is_channel_created_ped():
    # list = frappe.db.get_list("Project Employee Distribution", {"ped_from": "Opportunity", "is_channel_created" : "1"})
    # print(list)
    # print(len(list))
    # for i in list:
    #     print(i)
    #     ped_exist = frappe.db.exists("Project Employee Distribution", i["name"])
    #     print(ped_exist)
    #     if ped_exist:
    #         frappe.db.set_value('Project Employee Distribution',i["name"],
    #                         'is_channel_created',"1", update_modified=False)
    #         return i



    # list_is_created0 = list(set(["PED-26235", "PED-13120", "PED-13316",
    #         "PED-27028", "PED-27033", "PED-27050","PED-13273",
    #         "PED-13230","PED-13234","PED-13650","PED-14056",
    #         "PED-26335","PED-27030","PED-27031","PED-27568",
    #         "PED-27642", "PED-14769", "PED-25865",
    #         "PED-26365", "PED-27617", "PED-27649"]))

    # c = []
    # list = frappe.db.get_list("Project Employee Distribution",
    #                           {"ped_from": "Opportunity", "is_channel_created" : "1"})
    # for i in list:
    #     a = frappe.db.get_value("Project Employee Distribution", i["name"], "opportunity")
    #     b = frappe.db.get_value("Opportunity", a, ["name","proposal_name"], as_dict= True)
    #     # print(a,b)
    #     channel_name = b["proposal_name"].lower().replace(" ", "_")
    #     channel_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", channel_name)[:80]
    #     b["proposal_name"] = channel_name
    #     c.append(b)
    # for j in c:
    #     frappe.db.set_value('Opportunity',j["name"],
    #                                 "custom_channel_name", j["proposal_name"], update_modified=False)
        # return j


    return "Done"


def modify_is_channel_created():
    list_is_created0 = list(set(["PED-13113"]))
    for i in list_is_created0:
        # doc = frappe.get_doc("Project Employee Distribution", i)
        # doc.save()
        frappe.db.set_value('Project Employee Distribution',i,
                                'is_channel_created',"1", update_modified=False)
    return "Done"


def get_list_of_ped():
    result_list = []

    list = [{'ped_name': 'PED-27918', 'opportunity_id': 'CRM-OPP-2024-01029'}, {'ped_name': 'PED-27916', 'opportunity_id': 'CRM-OPP-2024-01028'}, {'ped_name': 'PED-27913', 'opportunity_id': 'CRM-OPP-2024-01106'}, {'ped_name': 'PED-27915', 'opportunity_id': 'CRM-OPP-2024-00991'}, {'ped_name': 'PED-27914', 'opportunity_id': 'CRM-OPP-2024-00908'}, {'ped_name': 'PED-27907', 'opportunity_id': 'CRM-OPP-2024-00918'}, {'ped_name': 'PED-27908', 'opportunity_id': 'CRM-OPP-2024-00805'}, {'ped_name': 'PED-27906', 'opportunity_id': 'CRM-OPP-2024-00803'}, {'ped_name': 'PED-27905', 'opportunity_id': 'CRM-OPP-2024-01108'}, {'ped_name': 'PED-27897', 'opportunity_id': 'CRM-OPP-2024-01001'}, {'ped_name': 'PED-27869', 'opportunity_id': 'CRM-OPP-2024-00937'}, {'ped_name': 'PED-27895', 'opportunity_id': 'CRM-OPP-2024-01105'}, {'ped_name': 'PED-27856', 'opportunity_id': 'CRM-OPP-2024-01000'}, {'ped_name': 'PED-27868', 'opportunity_id': 'CRM-OPP-2024-00909'}, {'ped_name': 'PED-27867', 'opportunity_id': 'CRM-OPP-2024-01031'}, {'ped_name': 'PED-27864', 'opportunity_id': 'CRM-OPP-2024-01030'}, {'ped_name': 'PED-27866', 'opportunity_id': 'CRM-OPP-2024-00990'}, {'ped_name': 'PED-27841', 'opportunity_id': 'CRM-OPP-2024-00719'}, {'ped_name': 'PED-27789', 'opportunity_id': 'CRM-OPP-2024-00904'}, {'ped_name': 'PED-27790', 'opportunity_id': 'CRM-OPP-2024-00903'}, {'ped_name': 'PED-27780', 'opportunity_id': 'CRM-OPP-2024-00789'}, {'ped_name': 'PED-27855', 'opportunity_id': 'CRM-OPP-2024-00992'}, {'ped_name': 'PED-27838', 'opportunity_id': 'CRM-OPP-2024-00969'}, {'ped_name': 'PED-27788', 'opportunity_id': 'CRM-OPP-2024-00833'}, {'ped_name': 'PED-27847', 'opportunity_id': 'CRM-OPP-2024-00920'}, {'ped_name': 'PED-27840', 'opportunity_id': 'CRM-OPP-2024-00733'}, {'ped_name': 'PED-27842', 'opportunity_id': 'CRM-OPP-2024-00905'}, {'ped_name': 'PED-27839', 'opportunity_id': 'CRM-OPP-2024-00767'}, {'ped_name': 'PED-27818', 'opportunity_id': 'CRM-OPP-2024-00774'}, {'ped_name': 'PED-27710', 'opportunity_id': 'CRM-OPP-2024-00770'}, {'ped_name': 'PED-27816', 'opportunity_id': 'CRM-OPP-2024-00907'}, {'ped_name': 'PED-27779', 'opportunity_id': 'CRM-OPP-2024-00779'}, {'ped_name': 'PED-27723', 'opportunity_id': 'CRM-OPP-2024-00784'}, {'ped_name': 'PED-27824', 'opportunity_id': 'CRM-OPP-2024-00782'}, {'ped_name': 'PED-27817', 'opportunity_id': 'CRM-OPP-2024-00775'}, {'ped_name': 'PED-27823', 'opportunity_id': 'CRM-OPP-2024-00832'}, {'ped_name': 'PED-27815', 'opportunity_id': 'CRM-OPP-2024-00804'}, {'ped_name': 'PED-27786', 'opportunity_id': 'CRM-OPP-2024-00812'}, {'ped_name': 'PED-27778', 'opportunity_id': 'CRM-OPP-2024-00809'}, {'ped_name': 'PED-27797', 'opportunity_id': 'CRM-OPP-2024-00769'}, {'ped_name': 'PED-27787', 'opportunity_id': 'CRM-OPP-2024-00921'}, {'ped_name': 'PED-27791', 'opportunity_id': 'CRM-OPP-2024-00906'}, {'ped_name': 'PED-27792', 'opportunity_id': 'CRM-OPP-2024-00913'}, {'ped_name': 'PED-27720', 'opportunity_id': 'CRM-OPP-2024-00632'}, {'ped_name': 'PED-27781', 'opportunity_id': 'CRM-OPP-2024-00734'}, {'ped_name': 'PED-27770', 'opportunity_id': 'CRM-OPP-2024-00780'}, {'ped_name': 'PED-27725', 'opportunity_id': 'CRM-OPP-2024-00811'}, {'ped_name': 'PED-27773', 'opportunity_id': 'CRM-OPP-2024-00729'}, {'ped_name': 'PED-27772', 'opportunity_id': 'CRM-OPP-2024-00730'}, {'ped_name': 'PED-27771', 'opportunity_id': 'CRM-OPP-2024-00790'}, {'ped_name': 'PED-27769', 'opportunity_id': 'CRM-OPP-2024-00838'}, {'ped_name': 'PED-27752', 'opportunity_id': 'CRM-OPP-2024-00806'}, {'ped_name': 'PED-27751', 'opportunity_id': 'CRM-OPP-2024-00837'}, {'ped_name': 'PED-27711', 'opportunity_id': 'CRM-OPP-2024-00807'}, {'ped_name': 'PED-27724', 'opportunity_id': 'CRM-OPP-2024-00710'}, {'ped_name': 'PED-27722', 'opportunity_id': 'CRM-OPP-2024-00562'}, {'ped_name': 'PED-27709', 'opportunity_id': 'CRM-OPP-2024-00810'}, {'ped_name': 'PED-27649', 'opportunity_id': 'CRM-OPP-2024-00714'}, {'ped_name': 'PED-27617', 'opportunity_id': 'CRM-OPP-2024-00679'}, {'ped_name': 'PED-13113', 'opportunity_id': 'CRM-OPP-2023-00514'}]
    print(len(list))
    count = 0
    for ped in list:
        # opportunity_id = frappe.db.get_value("Project Employee Distribution",
        #                                     ped["name"], "opportunity", as_dict=True)
        channel_name = frappe.db.get_value("Opportunity", ped["opportunity_id"],
                                        "custom_channel_name", as_dict=True)
        channel_id = frappe.db.get_value("Opportunity", ped["opportunity_id"],
                                        "custom_channel_id", as_dict=True)
        # channel_id = get_channel_id(channel_name["custom_channel_name"])
        # frappe.db.set_value('Opportunity',opportunity_id["opportunity"],
        #                         "custom_channel_id",channel_id, update_modified=False)
        # Create a dictionary containing the data along with channel_id
        data_with_channel_id = {
            "ped_name": ped["ped_name"],
            "opportunity_id": ped["opportunity_id"],
            "channel_name": channel_name["custom_channel_name"],
            "channel_id": channel_id["custom_channel_id"]
        }

        # Append the dictionary to the result list
        result_list.append(data_with_channel_id)
        # print(data_with_channel_id)
        count += 1
        print (count)

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
