import random
from models import *
from services.member_service import MemberService
from services.rate_service import RateService
from services.user_service import UserService
from services.milkcollection_service import MilkCollectionService
from configuration_manager import ConfigurationManager
from datetime import datetime


def frange(start, stop, step=0.1):
  return [start+round(x*step,1) for x in range(0, ((stop-start)*10)+1) if start+round(x*step,1) <= stop]

class DefaultDbData:
    def __init__(self):
        pass

    def create_members(self):
        mservice = MemberService()

        for i in range(1,10):
            name = "John" + str(random.randint(0, 9999))
            mobile = str(random.randint(111111111, 999999999))
            member_id = mservice.add(name=name,
                                     cattle_type=CattleType.COW,
                                     mobile=mobile,
                                     created_by=1,
                                     created_at=datetime.now())

            member = mservice.get(member_id)

            collection = {}
            collection['member'] = member
            collection['shift'] = CollectionShift.MORNING
            collection['fat'] = 4.2
            collection['snf'] = 7.9
            collection['qty'] = 1.5
            collection['clr'] = 28.63
            collection['aw'] = 89.24
            collection['rate'] = 26.48
            collection['total'] = collection['rate'] * collection['qty']
            collection['created_at'] = datetime.now()
            collection['created_by'] = 1
            collection['status'] = True

            colService = MilkCollectionService()
            col_id = colService.add(collection)

    def datetime_test(self):
        from datetime import datetime
        from helpers.datetime_util import set_system_datetime

        d = datetime.now()
        print "BEFORE:", d
        time_tuple = (d.year,  # Year
                      d.month,  # Month
                      d.day + 1,  # Day
                      d.hour,  # Hour
                      d.minute,  # Minute
                      d.second,  # Second
                      d.microsecond,  # Millisecond
        )
        set_system_datetime(time_tuple)
        d = datetime.now()
        print "AFTER:", d


    def test_settings(self):
        configManager = ConfigurationManager()
        settings = {}

        settings[SystemSettings.LANGUAGE] = "en"
        settings[SystemSettings.SOCIETY_NAME] = "JEPPIAAR MILK COLLECTION CENTER"
        settings[SystemSettings.SOCIETY_ADDRESS] = "NO.6, Andiyur Post, Uthangarai Taluk, Krishnagiri - 635307."
        settings[SystemSettings.SOCIETY_ADDRESS1] = ""

        settings[SystemSettings.HEADER_LINE1] = "Milk center"
        settings[SystemSettings.HEADER_LINE2] = "address"
        settings[SystemSettings.HEADER_LINE3] = "phone"
        settings[SystemSettings.HEADER_LINE4] = ""

        settings[SystemSettings.FOOTER_LINE1] = ""
        settings[SystemSettings.FOOTER_LINE2] = "Thank you"

        settings[SystemSettings.SCALE_TYPE] = ScaleType.OPAL
        settings[SystemSettings.ANALYZER_TYPE] = AnalyzerType.ULTRA
        settings[SystemSettings.RATE_TYPE] = CollectionRateType.FAT

        settings[SystemSettings.BILL_OVERWRITE] = True
        settings[SystemSettings.MANUAL_FAT] = True
        settings[SystemSettings.MANUAL_SNF] = True
        settings[SystemSettings.MANUAL_QTY] = True
        settings[SystemSettings.PRINT_CLR] = False
        settings[SystemSettings.PRINT_WATER] = False
        settings[SystemSettings.PRINT_BILL] = True
        settings[SystemSettings.QUANTITY_2_DECIMAL] = True
        settings[SystemSettings.EXTERNAL_DISPLAY] = False
        settings[SystemSettings.COLLECTION_PRINTER_TYPE] = "Thermal"
        settings[SystemSettings.DATA_EXPORT_FORMAT] = "PDF"

        configManager.set_all_settings(settings)

        #settings = configManager.get_all_settings()
        #for k in settings.keys():
        #    print k, " = ", settings[k]

    def test_rate_setup(self):
        rate_service = RateService()
        rate_service.update_fat_collection_rate("COW",1,2.5,3.5,150)
        rate_service.update_fat_collection_rate("COW",2,3.6,4.5,170)
        rate_service.update_fat_collection_rate("COW",3,4.6,6.0,195)
        rate_service.update_fat_collection_rate("COW",4,6.1,22.0,205)

        rate_service.update_fat_collection_rate("BUFFALO",5,2.5,3.5,150)
        rate_service.update_fat_collection_rate("BUFFALO",6,3.6,4.5,170)
        rate_service.update_fat_collection_rate("BUFFALO",7,4.6,6.0,195)
        rate_service.update_fat_collection_rate("BUFFALO",8,6.1,22.0,205)

        rate_service.save_ts2_collection_rate("COW", 1, 5, 10, 150)
        rate_service.save_ts2_collection_rate("COW", 2, 10.1, 11, 185)
        rate_service.save_ts2_collection_rate("COW", 3, 11.1, 13.5, 200)
        rate_service.save_ts2_collection_rate("COW", 4, 13.6, 22, 205)

        rate_service.save_ts2_collection_rate("BUFFALO", 5, 5, 10, 150)
        rate_service.save_ts2_collection_rate("BUFFALO", 6, 10.1, 11, 185)
        rate_service.save_ts2_collection_rate("BUFFALO", 7, 11.1, 13.5, 200)
        rate_service.save_ts2_collection_rate("BUFFALO", 8, 13.6, 22, 205)

        data = []
        for fat in frange(3, 12):
          for snf in frange(7,22):
            data.append({ "fat_value": fat, 
                          "snf_value": snf, 
                          "rate":20.0+random.random()})

        rate_service.set_fat_and_snf_collection_rate(cattle_type="COW",data=data)
        rate_service.set_fat_and_snf_collection_rate(cattle_type="BUFFALO",data=data)


    def create_default_users(self):
        user_service = UserService()
        created_by = 4
        created_at=datetime.now()
        user_service.add("basic", "$1$yWq10SD.$WQlvdj6kmHOY9KjHhuIGn1", "basic@milkpos.in", ["basic"], created_by, created_at)
        user_service.add("setup", "$1$Ii9Edtkd$cpxJMzTgpCmFxEhka2nKs/", "setup@milkpos.in", ["setup"], created_by, created_at)
        user_service.add("support", "$1$P/A0YAOn$O8SuzMiowBVJAorhfY239/", "support@milkpos.in", ["support"], created_by, created_at)
        user_service.add("admin", "$1$doG2/gED$vTLr/Iob7T9z0.nydnJxD1", "admin@milkpos.in", ["admin"], created_by, created_at)
