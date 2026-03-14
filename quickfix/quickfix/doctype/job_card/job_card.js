// Copyright (c) 2026, nivithamerlin and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Card", {
    refresh: function(frm) {
        if (frm.doc.status === "Ready for Delivery" && frm.doc.docstatus === 1) {
            frm.add_custom_button("Mark as Delivered", function() {
                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "Job Card",
                        name: frm.doc.name,
                        fieldname: "status",
                        value: "Delivered"
                    },
                    callback: function() {
                        frm.reload_doc();

                    }
                });
            });
            frm.add_custom_button("Reject Job", function() {

                let d = new frappe.ui.Dialog({
                    title: "Reject Job",
                    fields: [
                        {
                            label: "Rejection Reason",
                            fieldname: "reason",
                            fieldtype: "Small Text",
                            reqd: 1
                        }
                    ],
                    primary_action_label: "Submit",
                    primary_action(values) {

                        frappe.msgprint("Reason: " + values.reason);

                        d.hide();
                    }
                });

                d.show();

            });
            frm.add_custom_button("Transfer Technician", function() {

                frappe.prompt(
                    [
                        {
                            label: "New Technician",
                            fieldname: "technician",
                            fieldtype: "Link",
                            options: "Technician",
                            reqd: 1
                        }
                    ],
                    function(values) {

                        frappe.confirm(
                            "Are you sure you want to transfer this job?",
                            function() {

                                frappe.call({
                                    method: "frappe.client.set_value",
                                    args: {
                                        doctype: "Job Card",
                                        name: frm.doc.name,
                                        fieldname: "assigned_technician",
                                        value: values.technician
                                    },
                                    callback: function() {
                                        frm.reload_doc();
                                        frm.trigger("assigned_technician");
                                    }
                                });

                            }
                        );

                    },
                    "Transfer Technician",
                    "Transfer"
                );

            });

        }

        let shop_name = frappe.boot.quickfix_shop_name;

        if (shop_name) {
            frm.set_intro("Welcome to " + shop_name, "blue");
        }
    },
    assigned_technician: function(frm) {

        if (!frm.doc.assigned_technician) return;

        frappe.db.get_value(
            "Technician",
            frm.doc.assigned_technician,
            "specialization"
        ).then(r => {

            let specialization = r.message.specialization;

            if (specialization && specialization !== frm.doc.device_type) {

                frappe.msgprint(
                    "Warning: Technician specialization does not match the selected Device Type"
                );

            }

        });
    },
    quantity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let total = row.quantity * row.unit_price;
        frappe.model.set_value(cdt, cdn, "total_price", total);
    },
    
    setup: function(frm) {
        frm.set_query("assigned_technician", function() {
            return {
                filters: {
                    status: "Active",
                    specialization: frm.doc.device_type
                }
            };
        });
    },
    onload: function(frm) {
        frappe.realtime.on("job_ready", function(data) {
            frappe.show_alert({
                message: "Job is ready",
                indicator: "green"
            });
        });
    }
});