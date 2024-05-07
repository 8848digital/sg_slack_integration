import requests
import frappe
import re

token = frappe.db.get_single_value('Token', 'token')

def rename_channel(channel_id, new_name):
    url = "https://slack.com/api/conversations.rename"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "channel": channel_id,
        "name": new_name
    }
    response = requests.post(url, headers=headers, json=data)
    print (response.json())
    return response.json()


# @frappe.whitelist(allow_guest = True)
# def get_channel_id():

#     project_list = frappe.get_list("Project", fields=["name", "project_name"])
#     for item in project_list:
#         item["channel_name"] = item["name"].lower().replace(' ', '_')
#         item["project_name"] = item["project_name"].lower().replace(' ', '_')
#         item["project_name"] = re.sub(r'[^\w\d\u0620-\u06FF-]', '', item["project_name"])[:80]
#     # print(project_list)
#     # return "project_list"
#     token = frappe.db.get_single_value('Token', 'token')

#     if token:
#         url = "https://slack.com/api/conversations.list"
#         headers = {
#             'Authorization': f'Bearer {token}',
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }
#         payload = {
#             "limit": 999,
#             "types": "public_channel, private_channel"
#         }
#         try:
#             response = requests.request("POST",url, headers=headers, data=payload)
#             res = response.json()

#             channels_to_rename = {}
#             for i in res["channels"]:
#                 for j in project_list:

#                     if i["name"] == j["channel_name"]:
#                         channels_to_rename.update({i["id"]: j["channel_name"]})
#             print(channels_to_rename)
#             return "channels_to_rename"
#             # if channels_to_rename:
#             #     for channel_id, new_name in channels_to_rename.items():
#             #         response = rename_channel(channel_id, new_name)
#             #         if response["ok"]:
#             #             print(f"Channel {channel_id} renamed to {new_name}")
#             #         else:

#             #             print(f"Error renaming channel {channel_id}: {response['error']}")

#             # else:
#             #     return "No channel to rename"

#             # return channels_to_rename

#         except Exception as e:
#             frappe.log_error("An error occurred while setting topic:", str(e))
#     else:
#         frappe.throw("Please set Slack Token First")




def get_list_of_project():
    project_list = frappe.db.get_list("Project")
    print(len(project_list))
    to_exclude = ['PROJ-0020', 'PROJ-0908', 'PROJ-0418', 'PROJ-0931',
                  'PROJ-0928', 'PROJ-0892', 'PROJ-0898', 'PROJ-0905',
                  'PROJ-0933', 'PROJ-0901', 'PROJ-0513', 'PROJ-0930',
                  'PROJ-0895', 'PROJ-0945', 'PROJ-0940', 'PROJ-0942',
                  'PROJ-0929', 'PROJ-0907', 'PROJ-0899', 'PROJ-0934',
                  'PROJ-0941', 'PROJ-0924', 'PROJ-0906', 'PROJ-0909',
                  'PROJ-0932', 'PROJ-0896', 'PROJ-0897', 'PROJ-0921',
                  'PROJ-0944', 'PROJ-0904', 'PROJ-0939', 'PROJ-0943',
                  'PROJ-0922', 'PROJ-0982', 'PROJ-0983', 'PROJ-0995',
                  'PROJ-0962', 'PROJ-0996', 'PROJ-0965', 'PROJ-0959']
    print(len(to_exclude))
    project_list_filtered = [project for project in project_list if project['name'] not in to_exclude]
    # print (project_list_filtered)
    a = []
    output = []
    count = 0
    for project in project_list_filtered:
        project_name = frappe.db.get_value("Project", project["name"], "project_name", as_dict=True)
        channel_name = project_name["project_name"].lower().replace(" ", "_")
        channel_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", channel_name)[:80]

        channel_id = get_channel_id(channel_name)

        if channel_id ==None:
            a.append({project["name"]:channel_name})
            print ({project["name"]:channel_name})
        output.append({'name': project['name'], 'channel_name': channel_name, "channel_id": channel_id})
        # frappe.db.set_value("Project", project["name"], "custom_channel_name",
        #                     channel_name, update_modified=False)
        frappe.db.set_value("Project", project["name"], "custom_channel_id",
                            channel_id, update_modified=False)
        print ({'name': project['name'], 'channel_name': channel_name, "channel_id": channel_id})
        # return channel_name,project["name"], channel_id
        count += 1
        print(count)
    print(a)
    print(output)

    # return len(project_list_filtered)

def rename_remaining_project_channel():
    count = 0
    to_exclude = ['PROJ-0908', 'PROJ-0418', 'PROJ-0931',
                  'PROJ-0928', 'PROJ-0892', 'PROJ-0898', 'PROJ-0905',
                  'PROJ-0933', 'PROJ-0901', 'PROJ-0513', 'PROJ-0930',
                  'PROJ-0895', 'PROJ-0945', 'PROJ-0940', 'PROJ-0942',
                  'PROJ-0929', 'PROJ-0907', 'PROJ-0899', 'PROJ-0934',
                  'PROJ-0941', 'PROJ-0924', 'PROJ-0906', 'PROJ-0909',
                  'PROJ-0932', 'PROJ-0896', 'PROJ-0897', 'PROJ-0921',
                  'PROJ-0944', 'PROJ-0904', 'PROJ-0939', 'PROJ-0943',
                  'PROJ-0922', 'PROJ-0982', 'PROJ-0983', 'PROJ-0995',
                  'PROJ-0962', 'PROJ-0996', 'PROJ-0965', 'PROJ-0959']
    for project in to_exclude:
        print(count)
        print(project)
        # project_name = frappe.db.get_value("Project", project["name"], "project_name", as_dict=True)
        channel_name = project.lower().replace(" ", "_")
        channel_id = get_channel_id(channel_name)

        project_name = frappe.db.get_value("Project", project, "project_name")
        project_name = project_name.lower().replace(" ", "_")
        project_name = re.sub(r"[^\w\d\u0620-\u06FF-]", "", project_name)[:75]
        print(channel_id,project_name)
        rename = rename_channel(channel_id, project_name)
        if rename["ok"] == False and rename["error"] == "name_taken":
            count= 1
            while rename["ok"] != True:
                project_name = project_name + "_p"+ str(count)
                rename = rename_channel(channel_id, project_name)

        frappe.db.set_value("Project", project, "custom_channel_name", project_name)
        frappe.db.set_value("Project", project, "custom_channel_id", channel_id)
        count +=1
        # return







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