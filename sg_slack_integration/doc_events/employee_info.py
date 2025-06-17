import frappe
import requests
import json
import openai

from sg_slack_integration.doc_events.project_info import slack_response
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
                frappe.enqueue(
                    matching_employee_profile,
                    queue="long",
                    timeout=3600,
                    is_async=True,
                    job_name=f"Matching Employee Profile-{search_term}",
                    search_term=search_term,
                    response_url=response_url,
                    user_id=user_id,
                    req=req,
                    text=text
                )
                msg_block = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "⏳ Processing your request... You'll receive a response shortly."}
                    }
                ]
                slack_response(response_url,msg_block)
                


            else:
                msg_block=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "❌ Please provide valid parameters: `/start keywords`"}
                    }
                ]
                return slack_response(response_url, msg_block, user_id, "Success", req.get('command'), text, response="❌ Usage: `/start keyword`")
        else:
            msg_block=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "❌ Please ask slack admin to enable the seacrh api"}
                }
            ]
            return slack_response(response_url, msg_block, user_id, "Success", req.get('command'), text, response="❌ Usage: `/start keyword`")
                

    except Exception as e:
        frappe.log_error('Emp Search Result',frappe.get_traceback(e))
    
def matching_employee_profile(search_term,response_url,user_id,req,text):
    # search_term=get_search_term(search_term,settings_doc)
    settings_doc=frappe.get_doc('Slack Integration Settings')
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
                "text": {"type": "mrkdwn", "text": f"*These are the matched found for employee profile with keyword {search_term} *"}
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
        else:
            for match_data in matched_data:
                emp_profile=frappe.get_doc('Employee Profile',match_data)
                emp=frappe.get_doc('Employee',emp_profile.get('employee_id'))
                skills = frappe.get_all('Functional Skill',{'parent':emp_profile.get('name'),'parenttype': 'Employee Profile'},pluck='skills') if emp_profile.get('functional_skills') and frappe.db.exists('Functional Skill',{'parent':emp_profile.get('name'),'parenttype': 'Employee Profile'})  else ''
                all_skills=[s for s in skills if s!=None]
                content=f'''
                    Name ={emp_profile.get('employee_name')}\n
                    Designation = {emp_profile.get('employee_designation') if emp_profile.get('employee_designation') else ''}\n
                    Department = {emp.get('department') if emp.get('department') else ''}\n
                    Experience = {emp_profile.get('total_exp') if emp_profile.get('total_exp') else 0}\n
                    Skills={all_skills if all_skills else ''}
                '''
                msg_block.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{content or 'N/A'}"
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
    

def get_search_term(search_term,settings_doc):
    if not settings_doc:
        settings_doc=frappe.get_doc('Slack Integration Settings')
    if settings_doc.get('openai_key'):
        api_key = settings_doc.get('openai_key')
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract the search field and value from the user's request. Return JSON only."},
                {"role": "user", "content": search_term}
            ]
        )
        return response