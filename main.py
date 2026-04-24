#
#
import pymysql
import config as cfg

# Connect to the database
conn = pymysql.connect(
    host=cfg.mysql['host'],
    user=cfg.mysql['user'],
    password=cfg.mysql['password'],
    database=cfg.mysql['database']
)

cursor = conn.cursor()
close = conn.close()


#3.1.2 Display Main Menu

menu = input("Conference Management\n-------------------------\n\nMENU\n====\n1 - View Speaker and Sessions\n2 - View Attendees by Company\n3 - Add New Attendee\n4 - View Connected Attendees\n5 - Add Attendee Connection\n6 - View Rooms\nx - Exit Application\nChoice:")
print(menu)