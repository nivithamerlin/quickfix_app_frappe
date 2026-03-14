frappe.listview_settings["Job Card"] = {

    add_fields: ["status"],

    get_indicator: function(doc) {
        if (doc.status === "Draft") {
            return ["Draft", "orange"];
        }
        if (doc.status === "Pending Diagnosis") {
            return ["Pending Diagnosis", "yellow"];
        }
        if (doc.status === "Awaiting Customer Approval") {
            return ["Awaiting Customer Approval", "gray"];
        }
        if (doc.status === "In Repair") {
            return ["In Repair", "blue"];
        }
        if (doc.status === "Ready for Delivery") {
            return ["Ready for Delivery", "green"];
        }
        if (doc.status === "Delivered") {
            return ["Delivered", "purple"];
        }
        if (doc.status === "Cancelled") {
            return ["Cancelled", "red"];
        }
    }
    
};