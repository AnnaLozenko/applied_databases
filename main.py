# connect to database in MySQL
import mysql.connector
# handle errors
from mysql.connector import Error
# file with database credentials
import config as cfg


# ==========================================
# 1. VIEW SPEAKERS AND SESSIONS
# ==========================================
def view_speakers_and_sessions(cursor):
    search_string = input("Enter speaker's name (or part of it): ")
    query = """
            SELECT s.speakerName, s.sessionTitle, r.roomName
            FROM session s
                     JOIN room r ON s.roomID = r.roomID
            WHERE s.speakerName LIKE %s \
            """
    cursor.execute(query, (f"%{search_string}%",))
    results = cursor.fetchall()

    if not results:
        print("\nNo speakers were found of that name.")
    else:
        print(f"\nSession Details for: {search_string}\n{'-' * 44}")
        for row in results:
            speaker_name, session_title, room_name = row
            print(f"Speaker: {speaker_name}\nSession: {session_title}\nRoom: {room_name}\n")

# ========================================================
# 2. VIEW ATTENDEES BY COMPANY + HANDLING ERROR CONDITIONS
# ========================================================
def view_attendees_by_company(cursor):
    """Tasks 3 & 4: View Attendees by Company with Validation"""
    while True:
        user_input = input("\nEnter Company ID: ")

        # Validate numeric ID > 0
        if not user_input.isdigit() or int(user_input) <= 0:
            print("Invalid input. A valid company ID is any number greater than 0.")
            continue

        company_id = int(user_input)

        # Check if company exists
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company_row = cursor.fetchone()

        if not company_row:
            print(f"Company with ID {company_id} doesn't exist.")
            continue

        company_name = company_row[0]

        # Fetch attendees and their session details
        query = """
                SELECT a.attendeeName, a.attendeeDOB, s.sessionTitle, s.speakerName, r.roomName
                FROM attendee a
                         JOIN registration reg ON a.attendeeID = reg.attendeeID
                         JOIN session s ON reg.sessionID = s.sessionID
                         JOIN room r ON s.roomID = r.roomID
                WHERE a.attendeeCompanyID = %s \
                """
        cursor.execute(query, (company_id,))
        attendees = cursor.fetchall()
    # HANDLING ERROR CONDITIONS
        if not attendees:
            print(f"No attendees found for {company_name}")
            continue

        # If we reached here, everything is valid
        print(f"\nAttendees for {company_name}\n{'-' * 30}")
        for att in attendees:
            print(f"Name: {att[0]} | DOB: {att[1]}")
            print(f"Session: {att[2]}")
            print(f"Speaker: {att[3]} | Room: {att[4]}")
            print("-" * 20)
        break  # Exit the loop and return to main menu
# ==========================================
# 3. ADD NEW ATTENDEE + ERROR HANDLING
# ==========================================
def add_new_attendee(conn, cursor):

    print("\n--- Add New Attendee ---")

    # 1. Gather inputs from the user
    attendee_id = input("Enter Attendee ID: ")
    name = input("Enter Name: ")
    dob = input("Enter DOB (YYYY-MM-DD): ")
    gender = input("Enter Gender (Male/Female): ")
    company_id = input("Enter Company ID: ")

    # 2. Validate Gender first
    if gender not in ['Male', 'Female']:
        print("***ERROR***Gender must be Male/Female")
        return  # Exits the function and goes back to the main menu

    try:
        # 3. Check if Attendee ID already exists
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee_id,))
        if cursor.fetchone():
            print(f"***ERROR*** Attendee ID: {attendee_id} already exists")
            return

        # 4. Check if Company ID exists
        cursor.execute("SELECT companyID FROM company WHERE companyID = %s", (company_id,))
        if not cursor.fetchone():
            print(f"***ERROR***Company ID: {company_id} does not exist")
            return

        # 5. Insert the new attendee
        insert_query = """
                       INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID)
                       VALUES (%s, %s, %s, %s, %s) \
                       """
        cursor.execute(insert_query, (attendee_id, name, dob, gender, company_id))

        # MUST COMMIT to save the changes to the database
        conn.commit()
        print("Attendee successfully added")
    # CATCH ANY OTHER DATABASE ERRORS
    except Error as e:
        print(f"***ERROR***({e})")
        conn.rollback()  # Undo any pending changes if an error occurred


# ==========================================
# THE MAIN FUNCTION TO RUN THE APPLICATION
# ==========================================
# variables are initialized to "None", in case connection could not be established, to prevent program from crashing
def main():
    conn = None
    cursor = None
    # establish the connection
    try:
        conn = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )
        cursor = conn.cursor()
        # show the menu to the user
        while True:
            menu = input("\nConference Management\n-------------------------\n\nMENU\n====\n"
                         "1 - View Speakers and Sessions\n"
                         "2 - View Attendees by Company\n"
                         "3 - Add New Attendee\n"
                         "4 - View Connected Attendees\n"
                         "5 - Add Attendee Connection\n"
                         "6 - View Rooms\n"
                         "x - Exit Application\nChoice: ")

            if menu == '1':
                view_speakers_and_sessions(cursor)
            elif menu == '2':
                view_attendees_by_company(cursor)
            elif menu == '3':
                add_new_attendee(conn, cursor)
            elif menu.lower() == 'x':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    # handle errors
    except Error as e:
        print(f"Error: {e}")
    finally:
        # Only close if they were actually successfully created
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    main()