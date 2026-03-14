import frappe
import re
def get_context(context):
    context.title = "Track Your Repair Job"
    context.description = "Check repair status of your device"
    context.og_title = "Track Job - QuickFix"
    phone = frappe.form_dict.get("phone")
    if phone:
        phone = re.sub(r"\D", "", phone)
        if len(phone) == 10:
            context.jobs = frappe.db.get_list(
                "Job Card",
                filters={"phone": phone},
                fields=["name", "status", "device_model"],
                limit_page_length=5
            )