import frappe
from quickfix.quickfix.doctype.job_card.job_card import JobCard
class CustomJobCard(JobCard):
    def validate(self):
        super().validate()
        self._check_urgent_unassigned()
    def _check_urgent_unassigned(self):
        if self.priority == "Urgent" and not self.assigned_technician:
            settings = frappe.get_single("QuickFix Settings")
            frappe.enqueue("quickfix.utils.send_urgent_alert", job_card=self.name, manager=settings.manager_email)

"""
Method Resolution Order:
order in which python searches for methods when a class inherits from another class.
when validate() is called, python first checks CustomJobCard, then moves to JobCard

Why super().validate() is non-negotiable:
if we do not call super().validate()
1. Original JobCard validation will not run, field validations may break
2. System consistency may be corrupted
Therefore always call super() to preserve base behaviour
"""
"""
override_doctype_class vs doc_events
* completely replaces original Doctype python class
* Gives full control over all methods
* Cleaner for deep Customization
* Good for core logic modification

doc_events:
* Hooks into specific events (validate, on_submit etc)
* does not replace original class
* Good for adding small logic extensions
* Good for lightweight customizations
"""