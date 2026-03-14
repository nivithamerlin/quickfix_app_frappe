import frappe
from frappe.utils import date_diff

def execute(filters=None):
    frappe.enqueue(
        "quickfix.quickfix.report.technician_performance_report.technician_performance_report.run_report",
        filters=filters,
        queue="long"
    )

    return [], []
def run_report(filters=None):

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data)
    summary = get_report_summary(data)

    return columns, data, None, chart, summary
def get_columns(filters):
    columns = [
        {
            "label": "Technician",
            "fieldname": "technician",
            "fieldtype": "Link",
            "options": "Technician",
            "width": 150
        },
        {"label": "Total Jobs", "fieldname": "total_jobs", "fieldtype": "Int", "width": 120},
        {"label": "Completed", "fieldname": "completed", "fieldtype": "Int", "width": 120},
        {"label": "Avg Turnaround Days", "fieldname": "avg_turnaround", "fieldtype": "Float", "width": 150},
        {"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency", "width": 120},
        {"label": "Completion Rate %", "fieldname": "completion_rate", "fieldtype": "Percent", "width": 140}
    ]

    device_types = frappe.get_all("Device Type", fields=["name"])

    for dt in device_types:
        columns.append({
            "label": dt.name,
            "fieldname": dt.name.lower().replace(" ", "_"),
            "fieldtype": "Int",
            "width": 100
        })

    return columns

def get_data(filters):

    job_filters = {}

    if filters.get("from_date") and filters.get("to_date"):
        job_filters["creation"] = ["between", [filters.from_date, filters.to_date]]

    if filters.get("technician"):
        job_filters["assigned_technician"] = filters.technician

    jobs = frappe.get_list(
        "Job Card",
        fields=[
            "name",
            "assigned_technician",
            "status",
            "device_type",
            "estimated_cost",
            "creation",
            "completion_date"
        ],
        filters=job_filters
    )

    technicians = {}

    device_types = [d.name for d in frappe.get_all("Device Type", fields=["name"])]

    for job in jobs:

        tech = job.assigned_technician or "Unassigned"

        if tech not in technicians:
            technicians[tech] = {
                "technician": tech,
                "total_jobs": 0,
                "completed": 0,
                "revenue": 0,
                "turnaround_days": [],
            }

            for dt in device_types:
                technicians[tech][dt.lower().replace(" ", "_")] = 0

        technicians[tech]["total_jobs"] += 1

        if job.device_type:
            key = job.device_type.lower().replace(" ", "_")
            if key in technicians[tech]:
                technicians[tech][key] += 1

        if job.status == "Completed":
            technicians[tech]["completed"] += 1
            technicians[tech]["revenue"] += job.estimated_cost or 0

            if job.completion_date:
                days = date_diff(job.completion_date, job.creation)
                technicians[tech]["turnaround_days"].append(days)

    data = []

    for tech, values in technicians.items():

        total = values["total_jobs"]
        completed = values["completed"]

        avg_turnaround = 0
        if values["turnaround_days"]:
            avg_turnaround = sum(values["turnaround_days"]) / len(values["turnaround_days"])

        completion_rate = 0
        if total > 0:
            completion_rate = (completed / total) * 100

        row = {
            "technician": tech,
            "total_jobs": total,
            "completed": completed,
            "avg_turnaround": round(avg_turnaround, 2),
            "revenue": values["revenue"],
            "completion_rate": round(completion_rate, 2)
        }

        for key in values:
            if key not in row and key not in ["turnaround_days"]:
                row[key] = values[key]

        data.append(row)

    return data

def get_chart(data):

    labels = []
    total_jobs = []
    completed_jobs = []

    for row in data:
        labels.append(row["technician"])
        total_jobs.append(row["total_jobs"])
        completed_jobs.append(row["completed"])

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Total Jobs", "values": total_jobs},
                {"name": "Completed", "values": completed_jobs}
            ]
        },
        "type": "bar"
    }

    return chart

def get_report_summary(data):

    total_jobs = sum([d["total_jobs"] for d in data])
    total_revenue = sum([d["revenue"] for d in data])

    best_technician = None
    best_rate = 0

    for d in data:
        if d["completion_rate"] > best_rate:
            best_rate = d["completion_rate"]
            best_technician = d["technician"]

    summary = [
        {"label": "Total Jobs", "value": total_jobs, "indicator": "Blue"},
        {"label": "Total Revenue", "value": total_revenue, "indicator": "Green"},
        {"label": "Best Technician", "value": best_technician, "indicator": "Purple"}
    ]

    return summary

def formatter(value, row, column, data):

    if column.fieldname == "completion_rate":
        if value < 70:
            value = f'<span style="color:red">{value}</span>'
        elif value >= 90:
            value = f'<span style="color:green">{value}</span>'

    return value