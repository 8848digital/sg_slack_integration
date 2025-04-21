import frappe


@frappe.whitelist()
def get_leaderboard(start_date=None, end_date=None):
    if not start_date:
        start_date = frappe.utils.get_first_day(frappe.utils.nowdate())
    if not end_date:
        end_date = frappe.utils.get_last_day(frappe.utils.nowdate())

    results = frappe.db.sql("""
        SELECT slack_user_id, COUNT(*) as helpful_count
        FROM `tabKnowledge Helper Score`
        WHERE date BETWEEN %s AND %s
        GROUP BY slack_user_id
        ORDER BY helpful_count DESC
        LIMIT 10
    """, (start_date, end_date), as_dict=True)

    return results
