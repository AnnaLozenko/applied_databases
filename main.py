# connect to database in MySQL
import mysql.connector
# handle errors
from mysql.connector import Error
# file with database credentials
import config as cfg
# connect to Neo4j database
from neo4j import GraphDatabase


# ===============================
# 1. VIEW SPEAKERS AND SESSIONS
# ===============================
def view_speakers_and_sessions(cursor):
    '''

    The function shows speakers and sessions. The user is prompted to enter a speaker's name (or part of it),
    and the function retrieves and displays the speaker's name, session title, and room name for all matching records.
    If no speakers are found, an appropriate message is displayed.

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

    Retrieves and displays attendees belonging to a specific company.

    Prompts for a Company ID and joins the attendee, registration, session,
    and room tables to provide a full report. Includes validation for
    numeric IDs and existence checks.
    ---------------
    Parameters:
        cursor: MySQL cursor object.

    '''
    while True:
        # Validate ID is not blank (user must enter a value)
        user_input = input("\nEnter Company ID (or 'x' to go back): ").strip()

        #check for exit
        if user_input.lower() == 'x':
            break  # Exit the loop and return to main menu

        # Validate ID is numeric
        if not user_input or not user_input.isdigit():
            print("Invalid input. Please enter a numeric Company ID.")
            continue
        company_id = int(user_input)

        # Validate numeric ID > 0
        if company_id <= 0:
            print("Invalid input. Company ID must be greater than 0.")
            continue

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

    Prompts the user for details to create a new attendee record in MySQL.

    Validates that no fields are left empty, IDs are numeric, gender is
    correctly formatted, and that both the Attendee ID (must be unique)
    and Company ID (must exist) are valid.

    Parameters:
        conn: MySQL connection object (required for commit).
        cursor: MySQL cursor object.

    '''

    print("\n--- Add New Attendee ---")

    # 1. Gather and validate inputs from the user
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
# add check data types and that all data has been entered, not empty
    except Error as e:
        print(f"***ERROR***({e})")
        conn.rollback()  # Undo any pending changes if an error occurred


# ==============================================
# 4. VIEW CONNECTED ATTENDEES + HANDLING ERRORS
# ==============================================

def view_connected_attendees(mysql_cursor, neo4j_driver):
    '''
    Retrieves social connections for an attendee from Neo4j and MySQL.

    First validates the attendee exists in MySQL, then fetches their
    CONNECTED_TO neighbors from the Neo4j graph, and finally resolves
    those neighbor IDs back into names using MySQL.
    -------------
    Parameters:
        mysql_cursor: MySQL cursor object.
        neo4j_driver: Neo4j driver object.
    '''

    while True:
        user_input = input("\nEnter Attendee ID to view connections (or 'x' to go back): ").strip()

        if user_input.lower() == 'x':
            return

        # 1. Validation
        if not user_input or not user_input.isdigit():
            print("***ERROR*** Invalid Attendee ID. Please enter a number.")
            continue

        attendee_id = int(user_input)

        # 2. Check MySQL for existence
        mysql_cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
        result = mysql_cursor.fetchone()

        if not result:
            print("***ERROR*** Attendee does not exist.")
            continue

        attendee_name = result[0]
        print(f"\n--- Connections for {attendee_name} (ID: {attendee_id}) ---")

        # 3. Query Neo4j for connections
        # The syntax -[:CONNECTED_TO]- without an arrow means all connections are retrieved,
        # regardless of their direction.
        cypher_query = """
                    MATCH (a:Attendee {AttendeeID: $att_id})-[:CONNECTED_TO]-(b:Attendee)
                    RETURN b.AttendeeID AS connected_id
                """

        with neo4j_driver.session() as session:
            records = session.run(cypher_query, att_id=attendee_id)
            connected_ids = [record["connected_id"] for record in records]

        # 4. Handle results
        if not connected_ids:
            print("No connections found.")
            break

            # 5. Fetch names from MySQL
        for cid in connected_ids:
            mysql_cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (cid,))
            c_result = mysql_cursor.fetchone()
            if c_result:
                print(f"ID: {cid} | Name: {c_result[0]}")
        break

# =============================================
# 5. ADD ATTENDEE CONNECTION + HANDLING ERRORS
# =============================================
def add_attendee_connection(mysql_cursor, neo4j_driver):
    """
    This function adds a CONNECTED_TO relationship between two attendees.
    It first verifies that both attendees exist in the MySQL database.
    If they exist in MySQL, it ensures nodes for both attendees exist in Neo4j
    (creating them if they are missing using the MERGE function) and then creates
    the relationship, ensuring no duplicate connections or self-connections are made.

    """
    while True:
        id1_input = input("\nEnter first Attendee ID: ")
        id2_input = input("Enter second Attendee ID: ")

        # 1. Validation: verify that the inputs are numeric and not strings or empty
        if not id1_input.isdigit() or not id2_input.isdigit():
            print("***ERROR***Attendee IDs must be numbers.")
            continue

        id1 = int(id1_input)
        id2 = int(id2_input)

        # 2. Check self-connection
        if id1 == id2:
            print("***ERROR***An attendee cannot connect to him/herself.")
            continue

        # 3. Check MySQL database to ensure BOTH exist
        # Use IN (...) to check both at once. Since we proved id1 != id2 above,
        # len(results) must equal exactly 2 if both exist in MySQL.
        mysql_cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID IN (%s, %s)", (id1, id2))
        results = mysql_cursor.fetchall()

        if len(results) != 2:
            print("***ERROR*** One or both attendees IDs do not exist")
            continue

        # 4. Neo4j Operations
        with neo4j_driver.session() as session:
            # Check if they are ALREADY connected to prevent duplicates
            check_query = """
                MATCH (a:Attendee {AttendeeID: $id1})-[:CONNECTED_TO]-(b:Attendee {AttendeeID: $id2})
                RETURN a
            """
            existing_connection = session.run(check_query, id1=id1, id2=id2).data()

            if existing_connection:
                print("***ERROR***These attendees are already connected")
                continue

            # MERGE creates the node ONLY if it doesn't already exist in Neo4j database.
            create_query = """
                MERGE (a:Attendee {AttendeeID: $id1})
                MERGE (b:Attendee {AttendeeID: $id2})
                MERGE (a)-[:CONNECTED_TO]->(b)
            """
            session.run(create_query, id1=id1, id2=id2)

        print(f"Attendee {id1} is now connected to Attendee {id2}.")
        break

# ==================
# 6. VIEW ROOMS
# ==================

def view_rooms(cursor, room_cache):
    '''
    Displays all room details (ID, name, and capacity) using a caching mechanism.

    The first time the user selects this option, the data is fetched from the
    database and stored in the `room_cache` list. On subsequent selections,
    the data is loaded from the cache instead of querying the database again.
    Rooms added to the MySQL database after the initial fetch will not be
    visible unless the user exits and restarts the application.
    ----------------
    Parameters:
        cursor (mysql.connector.cursor.MySQLCursor): The database cursor to execute the query.
        room_cache (list): A list used to store cached room records in memory.
    ----------------
    Returns:
        None (Output is printed directly to the console).
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
    mysql_cursor = None
    neo4j_driver = None
    # connect to MySQL
    try:
        conn = mysql.connector.connect(
            host=cfg.mysql['host'],
            user=cfg.mysql['user'],
            password=cfg.mysql['password'],
            database=cfg.mysql['database']
        )
        mysql_cursor = conn.cursor()
        #connect to Neo4j
        neo4j_driver = GraphDatabase.driver(cfg.neo4j['uri'], auth=(cfg.neo4j['username'], cfg.neo4j['password']))
        # declare room_cache variable as empty list to store rooms data for caching mechanism in option 6
        room_cache = []
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
                view_speakers_and_sessions(mysql_cursor)
            elif menu == '2':
                view_attendees_by_company(mysql_cursor)
            elif menu == '3':
                add_new_attendee(conn, mysql_cursor)
            elif menu == '4':
                view_connected_attendees(mysql_cursor, neo4j_driver)
            elif menu == '5':
                add_attendee_connection(mysql_cursor, neo4j_driver)
            elif menu == '6':
                view_rooms(mysql_cursor, room_cache)
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
        if mysql_cursor:
            mysql_cursor.close()
        if conn and conn.is_connected():
            conn.close()
        if neo4j_driver:
            neo4j_driver.close()


if __name__ == "__main__":
    main()