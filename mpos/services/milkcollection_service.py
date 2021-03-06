from models import *
from datetime import datetime, date, timedelta
from db_manager import db
from sqlalchemy import Date, cast
from services.member_service import MemberService
from sqlalchemy.sql import func

class MilkCollectionService:
    def __init__(self):
        pass

    def add(self, entity):
        collection = MilkCollection(member=entity["member"]
            ,shift=entity["shift"],fat = entity["fat"],snf = entity["snf"]
            ,clr = entity["clr"],aw = entity["aw"],qty = entity["qty"]
            ,rate = entity["rate"],total = entity["total"], can_no=entity["can_no"]
            ,created_by = entity["created_by"], created_at = entity["created_at"],status = entity["status"])
        db.session.add(collection)
        db.session.commit()
        return collection.id

    def get(self, _id):
        entity = MilkCollection.query.filter_by(id=_id).one()
        # entity.member.name
        return entity

    def search(self, member_id=None, shift=None, created_at=None):
        query = MilkCollection.query
        if member_id and isinstance(member_id, int):
          query = query.filter_by(member_id=member_id)
        if shift and len(shift) > 0:
          query = query.filter_by(shift=shift)
        if created_at:
          start = created_at
          end = start + timedelta(days=1)
          query = query.filter(MilkCollection.created_at >= start)
          query = query.filter(MilkCollection.created_at < end)
        # query = query.order_by(MilkCollection.created_at.desc())
        query = query.order_by(MilkCollection.member_id)
        lst = query.all()
        return lst

    def search_by_date(self, member_id, from_date, to_date):
        query = MilkCollection.query
        if member_id and isinstance(member_id, int):
          query = query.filter_by(member_id=member_id)
        if from_date and to_date:
          to_date = to_date + timedelta(days=1)
          query = query.filter(MilkCollection.created_at >= from_date)
          query = query.filter(MilkCollection.created_at < to_date)
        query = query.order_by(MilkCollection.member_id)
        lst = query.all()
        return lst

    def update(self, _id, entity):
        collection = self.get(_id)
        #collection.member = entity["member"]
        collection.shift = entity["shift"]
        collection.fat = entity["fat"]
        collection.snf = entity["snf"]
        collection.clr = entity["clr"]
        collection.aw = entity["aw"]
        collection.qty = entity["qty"]
        collection.rate = entity["rate"]
        collection.total = entity["total"]
        collection.can_no = entity["can_no"]
        db.session.commit()

    def import_data(self, csv_data):
        pass

    def export_data(self):
        return None

    def clear_collection_bills(self, from_date=None, to_date=None):
      query = MilkCollection.query
      if from_date and to_date:
        query = query.filter(MilkCollection.created_at >= from_date)
        query = query.filter(MilkCollection.created_at < to_date)
      count = query.count()
      query.delete()
      db.session.commit()
      return count

    def get_total_litres(self, shift, can_no, created_at):
      query = db.session.query(func.sum(MilkCollection.qty))

      query = query.filter_by(can_no=can_no)
      query = query.filter_by(shift=shift)

      start = created_at
      end = start + timedelta(days=1)
      query = query.filter(MilkCollection.created_at >= start)
      query = query.filter(MilkCollection.created_at < end)

      return query.scalar() or 0.0

    def get_latest_can(self, shift, created_at):
      query = db.session.query(func.max(MilkCollection.can_no))

      query = query.filter_by(shift=shift)
      start = created_at
      end = start + timedelta(days=1)
      query = query.filter(MilkCollection.created_at >= start)
      query = query.filter(MilkCollection.created_at < end)

      return query.scalar() or 1

    def get_milk_collection_and_summary(self, shift, search_date):
      member_service = MemberService()
      member_list = member_service.search()
      members = {}
      for x in member_list:
        members[x.id] = x
      mcollection = self.search(None, shift=shift, created_at=search_date)

      cow_collection = [x for x in mcollection if members[x.member.id].cattle_type == "COW"]
      buffalo_collection = [x for x in mcollection if members[x.member.id].cattle_type == "BUFFALO"]
      summary = {}
      summary["member"] = [len(cow_collection),  len(buffalo_collection)]
      summary["milk"] = [sum([x.qty for x in cow_collection]), sum([x.qty for x in buffalo_collection])]
      summary["fat"] = [0,0]
      summary["snf"] = [0,0]
      summary["rate"] = [0,0]

      if summary["milk"][0] != 0:
        summary["fat"][0] = sum([x.fat*x.qty for x in cow_collection])/summary["milk"][0]
        summary["snf"][0] = sum([x.snf*x.qty for x in cow_collection])/summary["milk"][0]
        summary["rate"][0] = sum([x.rate*x.qty for x in cow_collection])/summary["milk"][0]

      if summary["milk"][1] != 0:
        summary["fat"][1] = sum([x.fat*x.qty for x in buffalo_collection])/summary["milk"][1]
        summary["snf"][1] = sum([x.snf*x.qty for x in buffalo_collection])/summary["milk"][1]
        summary["rate"][1] = sum([x.rate*x.qty for x in buffalo_collection])/summary["milk"][1]

      summary["total"] = [sum([x.total for x in cow_collection]), sum([x.total for x in buffalo_collection])]

      summary["grand"] = {}
      summary["grand"]["member"] = len(mcollection)
      summary["grand"]["qty"] = sum([x.qty for x in mcollection])
      summary["grand"]["total"] = sum([x.total for x in mcollection])
      summary["grand"]["fat"] = 0
      summary["grand"]["snf"] = 0
      summary["grand"]["rate"] = 0

      if summary["grand"]["qty"] != 0.0:
        summary["grand"]["fat"] = sum([x.fat*x.qty for x in mcollection])/summary["grand"]["qty"]
        summary["grand"]["snf"] = sum([x.snf*x.qty for x in mcollection])/summary["grand"]["qty"]
        summary["grand"]["rate"] = sum([x.rate*x.qty for x in mcollection])/summary["grand"]["qty"]

      return members, mcollection, summary
