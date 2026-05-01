# connect to database in MySQL
import mysql.connector
# handle errors
from mysql.connector import Error
# file with database credentials
import config as cfg


# ===============================
# 1. VIEW SPEAKERS AND SESSIONS
# ===============================
def view_speakers_and_sessions(cursor):
    '''
    The function shows speakers and sessions. The user is prompted to enter a speaker's name (or part of it),
    and the function retrieves and displays the speaker's name, session title, and room name for all matching records.
    If no speakers are found, an appropriate message is displayed.
    -----------------
    Parameters:
        cursor: MySQL cursor object
    -----------------
    Returns:
        speakers names, sessions, rooms names
    '''
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
    '''
    Shows attendees by company. User is prompted to enter the Company ID, and the function retrieves and
    displays the employee details (name, DOB, session, speaker, room) based on the user input.
    The function also includes error handling for invalid inputs and no attendees found.
    ----------------
    Parameters:
        cursor: mysql.connector.cursor
    ----------------
    Returns:
        employee details (name, DOB, session, speaker, room)
    '''
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
# ======================================
# 3. ADD NEW ATTENDEE + ERROR HANDLING
# ======================================
def add_new_attendee(conn, cursor):
    '''
    Add a new attendee to the attendees table. The user is prompted to enter the attendee ID, name, gender,
    DOB and Company ID.
    The function checks for the following error conditions:
    - If the gender input is invalid, an error message is displayed and the function exits without making any changes
        to the database.
    - If the attendee ID already exists in the database, an error message is displayed and the function exits without
        making any changes to the database.
    - If the company ID does not exist in the database, an error message is displayed and the function exits without
        making any changes to the database.
    ----------------
    Parameters:
        conn: the connection object to the MySQL database, used to commit changes
        cursor: the cursor object to execute SQL queries against the database
    ----------------
    Returns:
        commit new attendee to database based on user input, with error handling for invalid gender,
        duplicate attendee ID, and non-existent company ID
    '''
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


# =============================
# 4. VIEW CONNECTED ATTENDEES
# =============================


# =============================
# 5. ADD ATTENDEE CONNECTION
# =============================

# ==================
# 6. VIEW ROOMS
# ==================

def view_rooms(cursor, room_cache):
    '''
    Function to view all rooms details. The first time the user selects this option, the data is fetched from the
    database and stored in the room_cache list. On subsequent selections, the data is loaded from the cache instead of
    querying the database again. The rooms added to MySQL database after the user selected this option, will not be
    visible, unless the user exits and restarts the application.
    ------------
    Parameters:
        cursor:
        room_cache:
    ------------

    Returns: room ID, room name, room capacity.
        Details for all rooms with caching mechanism to avoid redundant database queries.

    '''
    print("\n--- View Rooms ---")

    # Check if cache is empty. If it is, this is the FIRST time
    # we are running this option, so we need to query the database.
    if not room_cache:
        print("(Fetching data from the database...)")
        cursor.execute("SELECT roomID, roomName, capacity FROM room")
        results = cursor.fetchall()

        # We use .extend() to add the database results into the cache list
        # This modifies the list so the main() function remembers it too.
        room_cache.extend(results)
    else:
        # If the cache is NOT empty, we skip the database entirely!
        print("(Loading data from memory...)")

    # Now, print whatever is in the cache
    if not room_cache:
        print("No rooms found in the database.")
    else:
        for room in room_cache:
            room_id, room_name, capacity = room
            print(f"Room ID: {room_id} | Name: {room_name} | Capacity: {capacity}")



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
            elif menu == '6':
                view_rooms(cursor, room_cache)
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