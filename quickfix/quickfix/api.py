import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Now
from datetime import timedelta, date
from frappe.utils import get_first_day, get_last_day, today
from frappe.client import get_count


def get_overdue_jobs():
    JC = DocType("Job Card")
    time = frappe.utils.now_datetime() - timedelta(days=7)
    result = (
        frappe.qb.from_(JC)
        .select(JC.name,JC.customer_name,JC.assigned_technician,JC.creation)
        .where((JC.status.isin(["Pending Diagnosis", "In Repair"])) &
            (JC.creation < time)
        )
        .orderby(JC.creation, order=frappe.qb.asc)
    ).run(as_dict=True)
    return result
@frappe.whitelist()
def transfer_job(from_tech, to_tech):
    try:
        frappe.db.sql("""
            UPDATE `tabJob Card`
            SET assigned_technician = %s
            WHERE assigned_technician = %s 
            AND status IN ('Pending Diagnosis', 'In Repair')
        """, (to_tech, from_tech))
        frappe.db.commit()
        return "Job cards transferred successfully"
    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(), "Job not transferred"
        )
        raise
@frappe.whitelist()
def share_job_card(job_card_name, user_email):
    print("Received name:", job_card_name)
    exists = frappe.db.exists("Job Card", job_card_name)
    print("Exists result:", exists)
    if not exists:
        frappe.throw(f"Job Card {job_card_name} not found")
    frappe.share.add(
        "Job Card",
        job_card_name,
        user_email,
        read=1
    )
    return "Shared successfully"
@frappe.whitelist()
def manager_only_action():
    frappe.only_for("QF Manager")
    return "This action is only for QF Managers"

def send_job_ready_email(job_card_name):
    job = frappe.get_doc("Job Card", job_card_name)
    frappe.sendmail(
        recipients=["nivithamerlin@gmail.com"],
        subject="Job Ready",
        message=f"Job Card {job.name} for {job.customer_name} is ready for delivery"
    )

def get_shop_name():
    shop = frappe.get_single("QuickFix Settings")
    return shop.shop_name
def format_job_id(value):
    return f"JOB#{value}"

@frappe.whitelist()
def custom_get_count(doctype, filters=None, debug=False, cache=False):
    frappe.get_doc({
        "doctype": "Audit Log",
        "doctype_name": doctype,
        "action": "count_queried",
        "user": frappe.session.user
    }).insert(ignore_permissions=True)
    return get_count(doctype, filters, debug, cache)

@frappe.whitelist()
def get_status_chart_data():

    data = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabJob Card`
        GROUP BY status
    """, as_dict=True)

    labels = []
    values = []

    for row in data:
        labels.append(row.status)
        values.append(row.count)

    return {
        "labels": labels,
        "datasets": [
            {
                "name": "Jobs",
                "values": values
            }
        ]
    }
@frappe.whitelist()
def get_shop_title():
    return 'QuickFix Mobile Repair'

def send_job_card_ready_email(job_card):
    doc = frappe.get_doc("Job Card", job_card)

    frappe.sendmail(
        recipients=doc.customer_email,
        subject="Your Device is Ready",
        message=f"Hello {doc.customer_name}, your device repair is complete."
    )
def generate_monthly_revenue():
    frappe.logger().info("Starting monthly revenue report")
    jobs = frappe.get_all(
        "Job Card",
        filters={"status": "Delivered"},
        fields=["name", "final_amount"]
    )
    total = 0
    for job in jobs:
        total += job.final_amount
    frappe.logger().info(f"Monthly Revenue: {total}")

def failing_background_job():
    x = 10/0
@frappe.whitelist(allow_guest=True)
def trigger_failure():
    frappe.enqueue(
        "quickfix.quickfix.api.failing_background_job",
        queue="default"
    )

def check_low_stock():
    last_run = frappe.db.get_value("Audit Log", {"action": "low_stock_check", "date": today()}, "name")
    if last_run:
        return
    parts = frappe.get_all("Spare Part", filters={"stock_qty": ["<", 5]}, fields=["name", "part_name", "stock_qty"])
    for part in parts:
        frappe.msgprint(f"Low stock alert: {part.part_name} has only {part.stock_qty} left in stock")

@frappe.whitelist(allow_guest=True)
def get_job_summary():
    job_card_name = frappe.form_dict.get("job_card_name")
    if not job_card_name:
        frappe.local.response["http_status_code"] = 400
        return {"error": "job_card_name is required"}
    job = frappe.db.get_value(
        "Job Card",
        job_card_name,
        ["name", "status", "assigned_technician", "creation"],
        as_dict=True
    )
    if not job:
        frappe.local.response["http_status_code"] = 404
        return {"error": "Job Card not found"}
    created_date = job.creation.date()
    return {
        "job_card": job.name,
        "name": job.name,
        "status": job.status,
        "assigned_technician": job.assigned_technician,
        "created_date": created_date
    }
@frappe.whitelist(allow_guest=True)
def get_job_by_phone():
    ip = frappe.local.request.remote_addr or "unknown"
    cache_key = f"rate_limit:{ip}"
    cache = frappe.cache()
    call_count = cache.get(cache_key)
    if not call_count:
        call_count = 0
    call_count = int(call_count)
    LIMIT = 10
    if call_count >= LIMIT:
        frappe.local.response["http_status_code"] = 429
        return {"error": "Too many requests, try again later"}
    cache.set(cache_key, call_count + 1, expires_in_sec=60)
    phone = frappe.form_dict.get("phone")
    if not phone:
        return {"error": "phone is required"}
    job = frappe.db.get_value(
        "Job Card",
        {"phone": phone},
        ["name", "status"],
        as_dict=True
    )
    if not job:
        frappe.local.response["http_status_code"] = 404
        return {"error": "Not found"}
    return job

def get_status_chart():
    cache_key = "job_card_status_chart"
    cached_data = frappe.cache().get_value(cache_key)
    if cached_data:
        return cached_data
    data = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabJob Card`
        GROUP BY status
    """, as_dict=True)
    frappe.cache().set_value(cache_key, data, expires_in_sec=300)
    return data

logger = frappe.logger("quickfix")
@frappe.whitelist(allow_guest=True)
def get_job_summary_details():
    try:
        job_card_name = frappe.form_dict.get("job_card_name")
        logger.info(f"API called with job card name: {job_card_name}")
        if not job_card_name:
            logger.warning("job_card_name parameter is missing")
            frappe.local.response["http_status_code"] = 400
            return {"error": "job_card_name is required"}
        job = frappe.db.get_value(
            "Job Card",
            job_card_name,
            ["name", "status", "assigned_technician"],
            as_dict=True
        )
        if not job:
            logger.warning(f"Job Card not found: {job_card_name}")
            return {"error": "Job Card not found"}
        logger.info(f"job card fetched successfully: {job}")
        return job
    except Exception:
        logger.error("Error occurred in get_job_summary_details API")
        frappe.log_error(
            title="Job summary API error",
            message=frappe.get_trackback()
        )
        return {"error": "Internal Server Error"}
