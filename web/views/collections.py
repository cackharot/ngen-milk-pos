from flask import render_template, request, redirect, g, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from dateutil import parser
import json
import os

from web import app, fmtDecimal, format_currency, get_currency_symbol, send_to_thermal_printer, settings_provider

from flask_babel import lazy_gettext
from services.member_service import MemberService
from services.milkcollection_service import MilkCollectionService
from services.rate_service import RateService
from services.rate_calc import RateCalc

from configuration_manager import ConfigurationManager

from models import *
from hal import *


def sendSms(entity):
  mobile = entity.member.mobile
  mobile = "+919789443696"
  #mobile = "+919952463624"
  
  tmp = app.jinja_env.get_template("thermal/ticket_sms.jinja2")
  data = settings_provider()
  data.update(entity=entity)
  markup = tmp.render(data)
  
  modem = SmsService(address="com4")
  modem.send(mobile, markup)


@app.route("/collection", methods=['GET', 'POST'])
@login_required
def collection():
  shift = "MORNING"
  date = datetime.now()

  changeDate = request.args.get("btnChangeDate", "False") == "True"

  if changeDate:
    day, month, year  = request.args.get("day", date.day), request.args.get("month", date.month), request.args.get("year", date.year)
    hour, minute, dn = request.args.get("hour", date.hour), request.args.get("minute", date.minute), request.args.get("dn", date.strftime("%p"))
    created_at = "%s/%s/%s %s:%s%s" % (day,month,year,hour,minute,dn)
    date1 = parser.parse(created_at, default=date, dayfirst=True)

    if date1 > date:
      flash(str(lazy_gettext("Date cannot be greater than today!")), "error")
    else:
      date = date1

  if date.hour >= 15:
    shift = "EVENING"

  member_service = MemberService()
  collectionService = MilkCollectionService()

  if request.method == "POST":
    entity = {}
    member_code = request.form.get("member_code")
    if member_code and len(member_code) > 0 and member_code.isdigit():
      mcode = int(member_code)
      collection_id = request.form.get("collection_id", None)
      entity["member"] = member_service.get(mcode)
      entity["shift"] = request.form.get("shift", shift)
      entity["fat"] = float(request.form.get("fat"))
      entity["snf"] = float(request.form.get("snf"))
      entity["clr"] = float(request.form.get("clr"))
      entity["aw"] = float(request.form.get("water"))
      entity["qty"] = float(request.form.get("qty"))
      entity["rate"] = float(request.form.get("rate"))
      entity["total"] = float(request.form.get("total"))
      entity["created_by"] = current_user.id
      entity["created_at"] = parser.parse(request.form.get("created_at", str(date)))
      entity["status"] = True
      if collection_id and int(collection_id) > 0:
        collectionService.update(int(collection_id), entity)
      else:
        collection_id = collectionService.add(entity)

      settings = g.app_settings
      can_print_bill = settings[SystemSettings.PRINT_BILL]
      saved_entity = collectionService.get(collection_id)
      if can_print_bill and (can_print_bill == "True" or bool(can_print_bill)):
        try:
          printTicket(saved_entity)
        except Exception as e:
          print "print exception:", e
          flash(str(lazy_gettext("Error in printing!")), "error")

      sendSms(saved_entity)

      flash("Saved successfully!", "success")
    else:
      flash("Invalid data!", "error")
    return redirect("/collection")
  
  member_list = member_service.search()
  members_json = json.dumps([{'id': x.id, 'name': x.name, 'cattle_type': x.cattle_type} for x in member_list])

  collection_members, mcollection, summary = collectionService.get_milk_collection_and_summary(shift, date.date())

  qty_total = 38.0
  t_qty = summary["milk"][0] + summary["milk"][1]
  t_qty = (1 - ((qty_total - t_qty)/qty_total))*100.0
  
  currency_symbol = get_currency_symbol()

  return render_template('collection.jinja2',
    shift=shift,
    member_list=member_list,
    members_json=members_json,
    date=date,
    collection_members=collection_members,
    summary=summary,
    t_qty=t_qty,
    currency_symbol=currency_symbol)


@app.route("/get_collection_data")
@login_required
def get_collection_data():
  member_id = request.args.get("member_id", None)
  shift = request.args.get("shift", None)
  cattle_type = request.args.get("cattle_type", "COW")
  today = datetime.now()
  created_at = parser.parse(request.form.get("created_at", str(today))).date()
  data = { "collection_id": None, "currency_symbol": get_currency_symbol() }

  if member_id and int(member_id) > 0 and shift and created_at:
    collectionService = MilkCollectionService()
    lst = collectionService.search(member_id=int(member_id), shift=shift, created_at=created_at)
    if lst and len(lst) > 0:
      entity = lst[0]
      data["collection_id"] = entity.id
      data["shift"] = entity.shift
      data["member_id"] = entity.member.id
      data["cattle_type"] = entity.member.cattle_type
      data["created_at"] = entity.created_at
      data["fat"] = entity.fat
      data["snf"] = entity.snf
      data["clr"] = entity.clr
      data["water"] = entity.aw
      data["qty"] = entity.qty
      data["rate"] = entity.rate
      data["total"] = entity.total
      data["fmt_rate"] = format_currency(entity.rate)
      data["fmt_total"] = format_currency(entity.total)
      override = request.args.get("override", "False")
      if override == "False":
        return jsonify(**data)

  rateCalc = RateCalc(g.app_settings[SystemSettings.RATE_TYPE])
  
  sensor_data = get_sensor_data()

  fat = data["fat"] = fmtDecimal(sensor_data["fat"])
  snf = data["snf"] = fmtDecimal(sensor_data["snf"])
  data["clr"] = fmtDecimal(sensor_data["clr"])
  data["water"] = fmtDecimal(sensor_data["water"])

  qty = data["qty"] = fmtDecimal(sensor_data["qty"])

  rate = fmtDecimal(rateCalc.get_rate(cattle_type, fat, snf))
  total = fmtDecimal(rate * qty)

  data["rate"] = rate
  data["total"] = total
  data["fmt_rate"] = format_currency(rate)
  data["fmt_total"] = format_currency(total)
  return jsonify(**data)


@app.route("/get_qty_data")
@login_required
def get_qty_data():
  member_id = request.args.get("member_id", None)
  shift = request.args.get("shift", None)
  cattle_type = request.args.get("cattle_type", "COW")
  today = datetime.now()
  created_at = parser.parse(request.form.get("created_at", str(today))).date()
  if member_id and int(member_id) > 0 and shift and created_at:
    collectionService = MilkCollectionService()
    lst = collectionService.search(member_id=int(member_id), shift=shift, created_at=created_at)
    if lst and len(lst) > 0:
      return jsonify({"status" : "failure"})

  settings = g.app_settings
  scale = WeightScale(settings[SystemSettings.SCALE_TYPE], address="/dev/ttyUSB1")
  qty = scale.get()
  qty = 0.0
  return jsonify({"status" : "success", "value": qty})


@app.route("/get_manual_data")
@login_required
def get_manual_data():
  cattle_type = request.args.get("cattle_type", "COW")
  rateCalc = RateCalc(g.app_settings[SystemSettings.RATE_TYPE])
  
  fat = float(request.args.get("fat", 0.0))
  snf = float(request.args.get("snf", 0.0))
  qty = float(request.args.get("qty", 0.0))
  clr = 4.0*(snf - (0.21 * fat)) - 0.36
  S = 8.5
  if cattle_type != "COW":
    S = 9.0
  aw = (((S-snf)/S)*100.0) - 0.7

  rate = fmtDecimal(rateCalc.get_rate(cattle_type, fat, snf))
  total = fmtDecimal(rate * qty)

  data = { "status" : "success", "currency_symbol": get_currency_symbol() }
  data["clr"] = fmtDecimal(clr)
  data["water"] = fmtDecimal(aw)
  data["rate"] = rate
  data["total"] = total
  data["fmt_rate"] = format_currency(rate)
  data["fmt_total"] = format_currency(total)
  return jsonify(data)


def get_sensor_data():
  settings = g.app_settings
  scale = WeightScale(settings[SystemSettings.SCALE_TYPE], address="/dev/ttyUSB1")
  analyzer = MilkAnalyzer(settings[SystemSettings.ANALYZER_TYPE], address="/dev/ttyUSB2")
  data = analyzer.get()
  data["qty"] = scale.get()
  return data


@app.route("/tare_scale")
@login_required
def tare_scale():
  settings = g.app_settings
  scale = WeightScale(settings[SystemSettings.SCALE_TYPE], address="/dev/ttyUSB1")
  success = scale.tare()
  return jsonify(success=success)


def printTicket(entity):
  tmp = app.jinja_env.get_template("thermal/ticket.jinja2")
  data = settings_provider()
  data.update(entity=entity)
  markup = tmp.render(data)
  send_to_thermal_printer(markup)