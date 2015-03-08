from flask import render_template, request, redirect, g, flash
from flask_login import login_required
from datetime import datetime, timedelta
from flask.ext.babel import lazy_gettext, gettext

from web import app

from services.member_service import MemberService
from services.rate_service import RateService
from services.milkcollection_service import MilkCollectionService
from models import *

@app.route("/reports")
@login_required
def reports():
  return render_template("reports.jinja2")


@app.route("/member_list")
@login_required
def report_member_list():
  member_service = MemberService()
  member_list = member_service.search()
  cow_member_list = [x for x in member_list if x.cattle_type == "COW"]
  buffalo_member_list = [x for x in member_list if x.cattle_type == "BUFFALO"]
  return render_template("member_list.jinja2",member_list=member_list,cow_member_list=cow_member_list,buffalo_member_list=buffalo_member_list)


@app.route("/absence_list")
@login_required
def absence_list():
  shift = request.args.get("shift", "MORNING")
  today = datetime.now().date()
  day   = int(request.args.get("day", today.day))
  month = int(request.args.get("month", today.month))
  year  = int(request.args.get("year", today.year))
  search_date = datetime(year, month, day).date()

  if search_date > today:
    search_date = today
    flash(str(lazy_gettext("Date cannot be greater than today!")), "error")

  collectionService = MilkCollectionService()
  lst = collectionService.search(created_at=search_date, shift=shift)

  member_service = MemberService()
  member_list = member_service.search()

  absence_members = []
  mids = [x.member_id for x in lst]
  for x in member_list:
    if not x.id in mids:
      absence_members.append(x)

  cow_member_list = [x for x in absence_members if x.cattle_type == "COW"]
  buffalo_member_list = [x for x in absence_members if x.cattle_type == "BUFFALO"]
  return render_template("absence_list.jinja2",member_list=absence_members,cow_member_list=cow_member_list,buffalo_member_list=buffalo_member_list,search_date=search_date,shift=shift)


@app.route("/detail_shift")
@login_required
def report_detail_shift():
  shift = request.args.get("shift", "MORNING")
  today = datetime.now().date()
  day   = int(request.args.get("day", today.day))
  month = int(request.args.get("month", today.month))
  year  = int(request.args.get("year", today.year))
  search_date = datetime(year, month, day).date()

  if search_date > today:
    search_date = today
    flash(str(lazy_gettext("Date cannot be greater than today!")), "error")

  collectionService = MilkCollectionService()
  members, mcollection, summary = collectionService.get_milk_collection_and_summary(shift, search_date)

  return render_template("detail_shift.jinja2", mcollection=mcollection, member_list=members, summary=summary, search_date=search_date, shift=shift)


@app.route("/shift_summary")
@login_required
def report_shift_summary():
  shift = request.args.get("shift", "MORNING")
  today = datetime.now().date()
  day   = int(request.args.get("day", today.day))
  month = int(request.args.get("month", today.month))
  year  = int(request.args.get("year", today.year))
  search_date = datetime(year, month, day).date()

  if search_date > today:
    search_date = today
    flash(str(lazy_gettext("Date cannot be greater than today!")), "error")

  collectionService = MilkCollectionService()
  members, mcollection, summary = collectionService.get_milk_collection_and_summary(shift, search_date)
  return render_template("shift_summary.jinja2", mcollection=mcollection, member_list=members, summary=summary, search_date=search_date, shift=shift)


@app.route("/payment_report")
@login_required
def payment_report():
  increment = float(request.args.get("increment", 0.0))
  end = datetime.now().date()
  start = end - timedelta(days=7)

  day   = int(request.args.get("from_day", start.day))
  month = int(request.args.get("from_month", start.month))
  year  = int(request.args.get("from_year", start.year))
  from_date = datetime(year, month, day).date()

  day   = int(request.args.get("to_day", end.day))
  month = int(request.args.get("to_month", end.month))
  year  = int(request.args.get("to_year", end.year))
  to_date = datetime(year, month, day).date()

  if to_date > end:
    to_date = end
    flash(str(lazy_gettext("To Date cannot be greater than today!")), "error")

  if to_date < from_date:
    to_date = end
    from_date = start
    flash(str(lazy_gettext("From Date cannot be greater than to date!")), "error")

  collectionService = MilkCollectionService()
  col_lst = collectionService.search_by_date(member_id=None,from_date=from_date,to_date=to_date)
  lst = {}
  summary = {"qty": 0.0, "rate": 0, "amount": 0, "increment": 0, "total": 0}

  for x in col_lst:
    if not x.member_id in lst.keys():
      inc = x.qty * increment
      total = x.total + inc
      lst[x.member_id] = { "qty": x.qty, "rate": x.rate, 
                           "fat": x.fat, "snf": x.snf, 
                           "amount": x.total, "increment": inc, "total": total}
    else:
      item = lst[x.member_id]
      item.qty = item.qty + x.qty
      item.rate = item.rate + x.rate
      item.fat = item.fat + x.fat
      item.snf = item.snf + x.snf
      item.amount = item.amount + x.amount
      item.increment = item.qty * increment
      item.total = item.amount + item.increment
    item = lst[x.member_id]
    summary["qty"] = summary["qty"] + item["qty"]
    summary["rate"] = summary["rate"] + item["rate"]
    summary["amount"] = summary["amount"] + item["amount"]
    summary["increment"] = summary["increment"] + item["increment"]
    summary["total"] = summary["total"] + item["total"]

  return render_template("payment_report.jinja2",from_date=from_date,to_date=to_date,lst=lst,increment=increment,summary=summary)