# Copyright (c) 2026, nivithamerlin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JobCard(Document):
	def validate(self):
		"""if len(self.customer_phone) != 10:
			frappe.throw("Customer Phone Number must be 10 digits long")"""
		if self.status == "In Repair" and not self.assigned_technician:
			frappe.throw("Technician must be assigned when status is 'In Repair'")
		self.calculate_total_price()
		self.set_labour_charge()
		self.set_final_amount()
	def calculate_total_price(self):
		total = 0
		for row in self.parts_used:
			row.total_price = row.quantity * row.unit_price
			total += row.total_price
		self.parts_total = total
	def set_labour_charge(self):
		if not self.labour_charge:
			labour = frappe.db.get_single_value("QuickFix Settings", "default_labour_charge")
			self.labour_charge = labour
	def set_final_amount(self):
		self.final_amount = self.parts_total + self.labour_charge
	def before_submit(self):
		if self.status != "Ready for Delivery":
			frappe.throw("Job Card can only be submitted when status is 'Ready for Delivery'")
		self.validate_stock_used()
	def validate_stock_used(self):
		for row in self.parts_used:
			available_qty = frappe.db.get_value("Spare Part", row.part, "stock_qty") or 0
			if row.quantity > available_qty:
				frappe.throw(f"Insufficient stock for {row.part}, available: {available_qty}, required: {row.quantity}")
	def on_submit(self):
		doc = frappe.get_doc({
			"doctype": "Service Invoice",
			"job_card": self.name,
			"customer_name": self.customer_name,
			"invoice_date": frappe.utils.nowdate(),
			"labour_charge": self.labour_charge,
			"parts_total": self.parts_total,
			"total_amount": self.final_amount,
			"status": self.status
		})
		doc.insert()
		self.calculate_current_stock()
		self.live_notify()
		self.email_update()
	def calculate_current_stock(self):
		for row in self.parts_used:
			current_stock = frappe.db.get_value("Spare Part", row.part, "stock_qty")
			new_stock = current_stock - row.quantity
			frappe.db.set_value("Spare Part", row.part, "stock_qty", new_stock, update_modified=True)
	def live_notify(self):
		frappe.publish_realtime(
			event="job_card_ready",
			message={
				"job_card": self.name,
				"customer": self.customer_name,
				"status": "Ready for Delivery"
				},
				user=self.owner
		)
	
	def email_update(self):
		frappe.enqueue(
			"quickfix.quickfix.api.send_job_ready_email",
			job_card_name=self.name,
			queue="short",
			timeout=300
		)
	def email_pdf_notification(self):
		pdf = frappe.get_print(
			"Job Card",
			self.name,
			print_format="Standard",
			as_pdf=True
		)
		frappe.sendmail(
			recipients=[self.customer_email, "nivithamerlin@gmail.com"],
			subject="Job Card Submitted",
			message="Pleasem find attached Job card Pdf",
			attachments=[{
				"fname": f"{self.name}.pdf",
				"fcontent": pdf
			}]
		)

	def on_cancel(self):
		self.status = "Cancelled"
		invoice_name = frappe.db.get_value("Service Invoice", {"job_card": self.name})
		if invoice_name:
			invoice = frappe.get_doc("Service Invoice", invoice_name)
			if invoice.docstatus == 1:
				invoice.cancel()
		self.restore_stock_qty()
	def restore_stock_qty(self):
		for row in self.parts_used:
			current_stock = frappe.db.get_value("Spare Part", row.part, "stock_qty")
			new_stock = current_stock + row.quantity
			frappe.db.set_value("Spare Part", row.part, "stock_qty", new_stock, update_modified=True)

	def on_trash(self):
		if self.status != "Cancelled" and self.status != "Draft":
			frappe.throw("cannot delete Job card unless its cancelled or in draft state")
	def on_update(self):
		if self.status == "Delivered":
			frappe.enqueue(
            	"quickfix.quickfix.api.send_job_ready_email",
        		queue="short",
            	job_card=self.name
            )
			frappe.enqueue(
    			"quickfix.quickfix.api.generate_monthly_revenue_report",
    			queue="long",
    			timeout=600
			)
			frappe.enqueue(
    			"quickfix.quickfix.api.generate_monthly_revenue_report",
    			year=2026,
    			queue="long", 
    			timeout=600   
			)
			frappe.enqueue(
    			"quickfix.quickfix.api.test_fail_job",
    			queue="long",
    			timeout=60
			)
		frappe.cache().delete_value("job_card_status_chart")