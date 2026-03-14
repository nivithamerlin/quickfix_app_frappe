# Copyright (c) 2026, nivithamerlin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, today
from datetime import datetime


class AuditLog(Document):
	pass
def log_entry(doc, method):
	if doc.doctype == "Audit Log":
		return
	frappe.get_doc({
		"doctype": "Audit Log",
		"doctype_name": doc.doctype,
		"document_name": doc.name,
		"action": method,
		"user": frappe.session.user,
		"timestamp": datetime.now()
	}).insert(ignore_permissions=True)
	"""def log_login(login_manager):
		frappe.get_doc({
			"doctype": "Audit Log",
			"doctype_name": "User",
			"document_name": frappe.session.user,
			"action": "Login",
			"user": frappe.session.user
		})
	def log_logout(login_manager):
		frappe.get_doc({
			"doctype": "Audit Log",
			"doctype_name": "User",
			"document_name": frappe.session.user,
			"action": "Logout",
			"user": frappe.session.user
		})"""
	def check_low_stock():
		last_run = frappe.db.get_value(
			"Audit Log",
			{"action": "low_stock_check", "timestamp": today()},
			"name"
		)
		if last_run:
			return
		frappe.get_doc({
			"doctype": "Audit Log",
			"action": "low_stock_check",
			"timestamp": today()
		})

