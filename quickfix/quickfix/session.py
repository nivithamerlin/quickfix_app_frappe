import frappe
def login_logger(login_manager):
    frappe.logger().info(
        f"User {frappe.session.user} logged in"
    )
def logout_logger(login_manager):
    frappe.logger().info(
        f"User {frappe.session.user} logged out"
    )