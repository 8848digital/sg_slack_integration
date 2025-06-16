import frappe
import requests
import json
import openai

from sg_slack_integration.doc_events.utils import create_slack_log_for_commands

@frappe.whitelist(allow_guest=True)
def get_info_emp_profile():
    try:
        req = frappe.form_dict
        settings_doc=frappe.get_doc('Slack Integration Settings')
        user_id = req.get("user_id") 
        response_url = req.get("response_url")
        search_term = req.get("text").strip()
        text=req.get("text")
        if settings_doc.get('enable_employee_details_search') and settings_doc.get('employee_app_id') and settings_doc.get('employee_app_id')==req.get('api_app_id'):
            if req.get('command')==settings_doc.get('search_command'):
                active_id=frappe.get_all('Employee',{'status':['!=','Inactive']},['name'],pluck='name')
                emp_profile=frappe.get_all('Employee Profile',['*'],{'employee_id':['in',active_id]})
                edu_qual=frappe.get_all('Educational Qualification',{'parenttype': 'Employee Profile'},['*'])
                rel_exp=frappe.get_all('Relevant Experience',{'parenttype': 'Employee Profile'},['*'])
                fun_skills=frappe.get_all('Functional Skill',{'parenttype': 'Employee Profile'},['*'])
                edu_qual_arabic=frappe.get_all('Educational Qualification Arabic',{'parenttype': 'Employee Profile'},['*'])

               
                matches_emp_profile = [
                    item['name']
                    for item in emp_profile
                    if any(
                        search_term.lower() in str(v).lower()
                        for v in item.values()
                    )
                ]
                match_edu=[
                    item['parent']
                    for item in edu_qual
                    if any(
                        search_term.lower() in str(v).lower()
                        for v in item.values()
                    )
                ]
                match_exp=[
                    item['parent']
                    for item in rel_exp
                    if any(
                        search_term.lower() in str(v).lower()
                        for v in item.values()
                    )
                ]
                match_fun_skills=[
                    item['parent']
                    for item in fun_skills
                    if any(
                        search_term.lower() in str(v).lower()
                        for v in item.values()
                    )
                ]
                match_edu_qual_arabic=[
                    item['parent']
                    for item in edu_qual_arabic
                    if any(
                        search_term.lower() in str(v).lower()
                        for v in item.values()
                    )
                ]
                matched_data=[]


                if len(matches_emp_profile):
                    matched_data=[a for a in matches_emp_profile]
                elif len(match_edu):
                    matched_data=[a for a in match_edu]
                elif len(match_exp):
                    matched_data=[a for a in match_exp]
                elif len(match_fun_skills):
                    matched_data=[a for a in match_fun_skills]
                elif len(match_edu_qual_arabic):
                    matched_data=[a for a in match_edu_qual_arabic]
                  
                   
                    
                if len(matched_data):
                    complete_profile=get_employee_profile_ai(matched_data,settings_doc)
                    msg_block = [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*These are the matched found for employee profile *"}
                        }
                    ]
                    if complete_profile:
                        for comp in complete_profile:

                            msg_block.append(
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": f"*{comp or 'N/A'}"
                                    }
                                }
                            )
                            
                        return slack_response(response_url, msg_block, user_id, "Success", req.get('command'), text, response=json.dumps(msg_block, indent=2))
                else:
                    msg_block=[
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": "❌ No Match found"}
                        }
                    ]
                    return slack_response(response_url, msg_block, user_id, "Success", req.get('command'), text, response=json.dumps(msg_block, indent=2))


            else:
                msg_block=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "❌ Please provide valid parameters: `/start keywords`"}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Usage: `/start keyword`")
        else:
            msg_block=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Please ask slack admin to enable the seacrh api"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.form.get('command'), text, response="❌ Usage: `/start keyword`")
                

    except Exception as e:
        frappe.log_error('Emp Search Result',e)
    



def slack_response(response_url, message_blocks, user_id=None, status=None, cmd=None, param=None, response=None, error=None):
    create_slack_log_for_commands(
        user=user_id, status=status, cmd=cmd, param=param, response=response, error=error)

    # Validate that message_blocks is a list
    if not isinstance(message_blocks, list):
        frappe.log_error("Invalid Blocks Format",
                         f"Expected list, got: {type(message_blocks)}")
        message_blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "⚠️ Invalid message format."}
            }
        ]

    # Sanitize each block
    sanitized_blocks = []
    for block in message_blocks:
        if not isinstance(block, dict) or "type" not in block or block["type"] != "section":
            frappe.log_error("Invalid Block", f"Block: {block}")
            continue
        text_obj = block.get("text", {})
        if not isinstance(text_obj, dict) or "type" not in text_obj or "text" not in text_obj:
            frappe.log_error("Invalid Text Object", f"Text: {text_obj}")
            continue
        text = str(text_obj.get("text") or "N/A")
        if not text.strip():
            frappe.log_error("Empty Block Text", f"Text: {text}")
            continue
        sanitized_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text[:3000]  # Truncate to Slack's 3000-char limit
            }
        })

    if not sanitized_blocks:
        sanitized_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "⚠️ No valid message content available."}
        })

    # Limit to 50 blocks (Slack's limit)
    sanitized_blocks = sanitized_blocks[:50]

    # Prepare the Slack API payload
    response = {
        "response_type": "ephemeral",
        "blocks": sanitized_blocks
    }

    # Log the payload for debugging
    frappe.log_error("Slack Payload", json.dumps(response, indent=2))

    # Send the request
    headers = {"Content-Type": "application/json"}
    result = requests.post(response_url, headers=headers, json=response)

    # Log the response
    frappe.log_error("Slack Response",
                     f"Status: {result.status_code}, Body: {result.text}")

    # Return a 200 OK response with an empty body
    # frappe.local.response["http_status_code"] = 200
    # frappe.local.response["content_type"] = "application/json"
    # frappe.local.response["data"] = ""
    return

def get_employee_profile_ai(matched_data,settings_doc=None):
    complete_details=[]
    frappe.log_error('Matched Data',matched_data)
    if not settings_doc:
        settings_doc=frappe.get_doc('Slack Integration Settings')
    if settings_doc.get('openai_key'):
        api_key = settings_doc.get('openai_key')
        client = openai.OpenAI(api_key=api_key)
        for i in matched_data:
            try:
                emp_profile=frappe.get_doc('Employee Profile',i)
                emp=frappe.get_doc('Employee',emp_profile.get('employee_id'))
                name =emp_profile.get('employee_name')
                designation =emp_profile.get('employee_designation') if emp_profile.get('employee_designation') else ''
                department = emp.get('department') if emp.get('department') else ''
                experience = emp_profile.get('total_exp') if emp_profile.get('total_exp') else 0
                skills = frappe.get_all('Functional Skill',{'parent':emp_profile.get('name'),'parenttype': 'Employee Profile'},pluck='skills') if emp_profile.get('functional_skills') and frappe.db.exists('Functional Skill',{'parent':emp_profile.get('name'),'parenttype': 'Employee Profile'})  else ''
                all_skills=[s for s in skills if s!=None]
                if all_skills:
                    content = (
                        f"Generate a professional employee profile for {name}, "
                        f"{designation}, {department} department, "
                        f"{experience} experience, skills in {', '.join(all_skills)}."
                    )
                else:
                    content = (
                        f"Generate a professional employee profile for {name}, "
                        f"{designation}, {department} department, "
                        f"{experience} experience."
                    )


                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "user", "content": content}
                    ]
                )
                # print(response)
                profile_text = response.choices[0].message.content
                if profile_text:
                    complete_details.append(profile_text)
            except Exception as e:
                frappe.log_error(f'get_employee_profile_ai',e)
            
        else:
            return complete_details
    
