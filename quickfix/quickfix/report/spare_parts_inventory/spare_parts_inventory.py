# Copyright (c) 2026, nivithamerlin and contributors
# For license information, please see license.txt

import frappe
def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    summary = get_report_summary(data)
    return columns, data, None, None, summary
def get_columns(filters=None):
	columns = [
		{"label": "Part Name", "fieldname": "part_name", "fieldtype": "Data", "width": 200},
        {"label": "Part Code", "fieldname": "part_code", "fieldtype": "Data", "width": 120},
        {"label": "Device Type", "fieldname": "device_type", "fieldtype": "Link", "options": "Device Type","width": 140},
        {"label": "Stock Qty", "fieldname": "stock_qty", "fieldtype": "Float", "width": 100},
        {"label": "Reorder Level", "fieldname": "reorder_level", "fieldtype": "Float", "width": 120},
        {"label": "Unit Cost", "fieldname": "unit_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Selling Price", "fieldname": "selling_price", "fieldtype": "Currency", "width": 120},
        {"label": "Margin %", "fieldname": "margin_percent", "fieldtype": "Percent", "width": 100},
        {"label": "Total Value", "fieldname": "total_value", "fieldtype": "Currency", "width": 120}
            
	]
	return columns
def get_data(filters=None):
	parts = frappe.get_list(
		"Spare Part",
		fields=[
			"part_name",
			"name as part_code",
			"device_type",
			"stock_qty",
			"reorder_level",
			"unit_cost",
			"selling_price"
		]
	)
	data = []
	total_stock = 0
	total_value = 0
	for part in parts:
		margin = 0
		if part.selling_price:
			margin = ((part.selling_price - part.unit_cost) / part.selling_price) * 100
		value = (part.stock_qty or 0) * (part.unit_cost or 0)
		total_stock += part.stock_qty or 0
		total_value += value
		row = {
			"part_name": part.part_name,
			"part_code": part.part_code,
			"device_type": part.device_type,
			"stock_qty": part.stock_qty,
			"reorder_level": part.reorder_level,
			"unit_cost": part.unit_cost,
			"selling_price": part.selling_price,
			"margin_percent": round(margin, 2),
			"total_value": round(value, 2)
		}
		data.append(row)
	data.append({
		"part_name": "TOTAL",
		"stock_qty": total_stock,
		"total_value": round(total_value, 2)
	})
	return data

def get_report_summary(data):
	parts = frappe.get_list(
		"Spare Part",
		fields=["stock_qty", "reorder_level", "unit_cost"]
	)
	total_parts = len(parts)
	below_reorder = 0
	inventory_value = 0
	for part in parts:
		if part.stock_qty < part.reorder_level:
			below_reorder += 1
		inventory_value += (part.stock_qty or 0) * (part.unit_cost or 0)
	summary = [
		{"label": "Total Parts", "value": total_parts, "indicator": "Blue"},
		{"label": "Below Reorder", "value": below_reorder, "indicator": "Red"},
		{"label": "Total Inventory Value", "value": round(inventory_value, 2), "indicator": "Green"}
	]
	return summary

def formatter(value, row, column, data):
	if data.stock_qty <= data.reorder_level:
		return f'<span style="background-color:#ffdddd">{value}</span>'
	return value
      
