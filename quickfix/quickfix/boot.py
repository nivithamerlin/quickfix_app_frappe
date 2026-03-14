import frappe
def boot_session(bootinfo):
    bootinfo.quickfix_version = "1.0"
    bootinfo.device_types = frappe.get_all(
        "Device Type",
        fields=["name"]
    )