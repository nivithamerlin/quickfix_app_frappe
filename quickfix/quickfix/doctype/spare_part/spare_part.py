# Copyright (c) 2026, nivithamerlin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SparePart(Document):
	def on_update(self):
		alert = frappe.db.get_single_value("QuickFix Settings", "low_stock_alert_enabled")
		
