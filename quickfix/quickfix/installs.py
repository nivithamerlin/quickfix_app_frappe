import frappe
def after_install():
    create_device_types()
    create_settings()
    frappe.make_property_setter(
        "Job Card",
        "remarks",
        "bold",
        1,
        "Check"
    )
    frappe.msgprint("Quickfix setup completed successfully")
def create_device_types():
    device_types = ["Latop", "Mobile", "Printer"]
    for d in device_types:
        if not frappe.db.exists("Device Type", d):
            doc = frappe.get_doc({
                "doctype": "Device Type",
                "device_type": d
            })
            doc.insert(ignore_permissions=True)
def create_setings():
    if not frappe.db.exists("QuickFix Settings"):
        doc = frappe.get_doc({
            "doctype": "QuickFix Settings",
            "setting_name": "Default Settings"
        })
        doc.insert(ignore_permissions=True)
def before_install():
    submitted_job_cards = frappe.db.count(
        "Job Card",
        {"docstatus": 1}
    )
    if submitted_job_cards > 0:
        frappe.throw(
            "Cannot uninstall Quickfix because submitted Job Cards exists",
            frappe.ValidationError
        )