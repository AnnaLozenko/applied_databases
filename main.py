# connect to database in MySQL
import mysql.connector
# handle errors
from mysql.connector import Error
# file with database credentials
import config as cfg
# connect to Neo4j database
from neo4j import GraphDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()
# ===============================
# 1. VIEW SPEAKERS AND SESSIONS
# ===============================
def view_speakers_and_sessions(cursor):
    """
    Search for speakers by name or part of a name.
    If 'x' is entered exactly, the function returns to the main menu.
    Otherwise, it searches and displays speaker, session title, and room name.
    """
    while True:
        # We use .strip() to ignore accidental leading/trailing spaces
        search_string = console.input("\n[bold cyan]Enter speaker's name (or 'x' to go back): [/bold cyan]").strip()

        # 1. Check for exit command first
        if search_string.lower() == 'x':
            return  # Returns to the main menu

        # 2. Check for empty input
        if not search_string:
            print("Search cannot be empty. Please enter a name or 'x' to exit.")
            continue

        query = """
                SELECT s.speakerName, s.sessionTitle, r.roomName
                FROM session s
                         JOIN room r ON s.roomID = r.roomID
                WHERE s.speakerName LIKE %s
                """

        cursor.execute(query, (f"%{search_string}%",))
        results = cursor.fetchall()

        if not results:
            rprint(f"[bold red]No speakers found with the name '{search_string}'.[/bold red]")
            # Loop continues so user can try again
        else:
            table = Table(title=f"Search Results for: {search_string}", style="cyan")
            table.add_column("Speaker", style="yellow")
            table.add_column("Session Title", style="white")
            table.add_column("Room", style="green")

            for row in results:
                table.add_row(row[0], row[1], row[2])

            console.print(table)

            # After showing results, loop back to allow another search
            # or 'x' to exit.

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
        # The .strip() removes any accidental spaces the user might type
        user_input = console.input("\n[bold cyan]Enter Company ID (or 'x' to go back): [/bold cyan]").strip()

        #check for exit
        if user_input.lower() == 'x':
            break  # Exit the loop and return to main menu

        # Validate ID is numeric
        if not user_input or not user_input.isdigit():
            rprint("[bold red]Invalid input. Please enter a numeric ID.[/bold red]")
            continue
        company_id = int(user_input)

        # Validate numeric ID > 0
        if company_id <= 0:
            console.print("[bold red]Invalid input. Company ID must be greater than 0.[/bold red]")
            continue

        # Check if company exists
        cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (company_id,))
        company_row = cursor.fetchone()

        if not company_row:
            rprint(f"[bold red]Company ID {company_id} not found.[/bold red]")
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
            rprint(f"[yellow]No attendees found for {company_row[0]}.[/yellow]")
            continue

        else:
            # Upgrade: Using a Table
            table = Table(title=f"Attendee Report: {company_row[0]}", style="magenta")
            table.add_column("Name", style="white")
            table.add_column("DOB", style="dim")
            table.add_column("Session", style="blue")
            table.add_column("Speaker", style="yellow")
            table.add_column("Room", style="green")

            for att in attendees:
                table.add_row(att[0], str(att[1]), att[2], att[3], att[4])

            console.print(table)

# ======================================
# 3. ADD NEW ATTENDEE + ERROR HANDLING
# ======================================
def add_new_attendee(conn, cursor):
    """
    Prompts the user for details to create a new attendee record in MySQL.

    Validates that no fields are left empty, IDs are numeric, gender is
    correctly formatted, and that both the Attendee ID (must be unique)
    and Company ID (must exist) are valid.
    """
    print("\n--- Add New Attendee ---")
    print("(Type 'x' at any prompt to cancel and return to menu)")

    # 1. Gather inputs from the user
    # The .strip() removes any accidental spaces the user might type
    attendee_id = console.input("[bold cyan]Enter Attendee ID: [/bold cyan]").strip()
    # go back to main menu if user typed in "x"
    if attendee_id.lower() == 'x':
        return

    name = console.input("[bold cyan]Enter Name: [/bold cyan]").strip()
    if name.lower() == 'x':
        return

    dob = console.input("[bold cyan]Enter DOB (YYYY-MM-DD): [/bold cyan]").strip()
    if dob.lower() == 'x':
        return

    gender = console.input("[bold cyan]Enter Gender (Male/Female): [/bold cyan]").strip()
    if gender.lower() == 'x':
        return

    company_id = console.input("[bold cyan]Enter Company ID: [/bold cyan]").strip()
    if company_id.lower() == 'x':
        return

    # 2. Check if ANY of the fields were left completely blank
    if attendee_id == "" or name == "" or dob == "" or gender == "" or company_id == "":
        console.print("[bold red]***ERROR*** No fields can be left empty.[/bold red]")
        return

    # 3. Check that the IDs are actually numbers
    if not attendee_id.isdigit() or not company_id.isdigit():
        console.print("[bold red]***ERROR*** Attendee ID and Company ID must be numeric.[/bold red]")
        return

    # 4. Check that Gender is exactly Male or Female
    if gender not in ['Male', 'Female']:
        console.print("[bold red]***ERROR*** Gender must be Male/Female[/bold red]")
        return

    # 5. Database Operations (Check existence, then Insert)
    try:
        # Convert IDs to integers now that we know they are safe numbers
        attendee_id_int = int(attendee_id)
        company_id_int = int(company_id)

        # Check if Attendee ID already exists
        cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (attendee_id_int,))
        if cursor.fetchone():
            console.print(f"[bold red]***ERROR*** Attendee ID: {attendee_id} already exists[/bold red]")
            return

        # Check if Company ID exists
        cursor.execute("SELECT companyID FROM company WHERE companyID = %s", (company_id_int,))
        if not cursor.fetchone():
            console.print(f"[bold red]***ERROR*** Company ID: {company_id} does not exist[/bold red]")
            return

        # Insert the new attendee
        insert_query = """
                       INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID)
                       VALUES (%s, %s, %s, %s, %s)
                       """
        cursor.execute(insert_query, (attendee_id_int, name, dob, gender, company_id_int))

        # COMMIT to save the changes to the database
        conn.commit()
        console.print("[green]Attendee successfully added[/green]")

    except Error as e:
        # This catches things like an invalid Date format (e.g., typing a string for DOB)
        print(f"[red]***ERROR***({e})[/red]")
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
        user_input = console.input("\n[bold cyan]Enter Attendee ID to view connections (or 'x' to go back): [/bold cyan]").strip()

        if user_input.lower() == 'x':
            return

        # 1. Validation
        if not user_input or not user_input.isdigit():
            console.print("[bold red]***ERROR*** Invalid Attendee ID. Please enter a number.[/bold red]")
            continue

        attendee_id = int(user_input)

        # 2. Check MySQL for existence
        mysql_cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attendee_id,))
        result = mysql_cursor.fetchone()

        if not result:
            console.print("[bold red]***ERROR*** Attendee does not exist.[/bold red]")
            continue

        attendee_name = result[0]
        console.print(f"\n[cyan]--- Connections for {attendee_name} (ID: {attendee_id}) ---[/cyan]")

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
            console.print("[yellow]No connections found.[/yellow]")
            break

            # 5. Fetch names from MySQL
        for cid in connected_ids:
            mysql_cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (cid,))
            c_result = mysql_cursor.fetchone()
            if c_result:
                console.print(f"[cyan]ID: {cid} | Name: {c_result[0]}[/cyan]")
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
        # Added the 'x' option and .strip() to clean the inputs
        id1_input = console.input("\n[bold cyan]Enter first Attendee ID (or 'x' to go back): [/bold cyan]").strip()
        if id1_input.lower() == 'x':
            return

        id2_input = console.input("[bold cyan]Enter second Attendee ID (or 'x' to go back): [/bold cyan]").strip()
        if id2_input.lower() == 'x':
            return

        # 1. Validation: verify that the inputs are numeric and not strings or empty
        if not id1_input.isdigit() or not id2_input.isdigit():
            console.print("[bold red]***ERROR***Attendee IDs must be numbers.[/bold red]")
            continue

        id1 = int(id1_input)
        id2 = int(id2_input)

        # 2. Check self-connection
        if id1 == id2:
            console.print("[bold red]***ERROR***An attendee cannot connect to him/herself.[/bold red]")
            continue

        # 3. Check MySQL database to ensure BOTH exist
        mysql_cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID IN (%s, %s)", (id1, id2))
        results = mysql_cursor.fetchall()

        if len(results) != 2:
            console.print("[bold red]***ERROR*** One or both attendees IDs do not exist[/bold red]")
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
                console.print("[bold red]***ERROR***These attendees are already connected[/bold red]")
                continue

            # MERGE creates the node ONLY if it doesn't already exist in Neo4j database.
            create_query = """
                MERGE (a:Attendee {AttendeeID: $id1})
                MERGE (b:Attendee {AttendeeID: $id2})
                MERGE (a)-[:CONNECTED_TO]->(b)
            """
            session.run(create_query, id1=id1, id2=id2)

        console.print(f"[bold green]Attendee {id1} is now connected to Attendee {id2}.[/bold green]")
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
        console.print("[bold cyan](Fetching data from the database...)[/bold cyan]")
        cursor.execute("SELECT roomID, roomName, capacity FROM room")
        results = cursor.fetchall()

        # We use .extend() to add the database results into the cache list
        # This modifies the list so the main() function remembers it too.
        room_cache.extend(results)
    else:
        # If the cache is NOT empty, we skip the database entirely!
        console.print("[bold green](Loading data from memory...)[/bold green]")

    # Now, print whatever is in the cache
    if not room_cache:
        print("No rooms found in the database.")
    else:

        table = Table(title="Available Rooms", style="cyan")
        table.add_column("Room ID", style="yellow")
        table.add_column("Name", style="white")
        table.add_column("Capacity", style="green")

        for row in room_cache:
            table.add_row(str(row[0]), str(row[1]), str(row[2]))

        console.print(table)
    input("\nPress Enter to return to menu...")

    # ===============================
# 7. INNOVATION: CONFERENCE DASHBOARD
# ===============================
def view_conference_dashboard(cursor):
    """
    Innovation Task: Provides a high-level analytical dashboard of the conference
    using SQL Aggregate functions.
    """
    try:
        # 1. Get Total Attendee Count
        cursor.execute("SELECT COUNT(*) FROM attendee")
        total_attendees = cursor.fetchone()[0]

        # 2. Get Most Popular Session
        cursor.execute("""
                       SELECT s.sessionTitle, COUNT(r.registrationID) as count
                       FROM session s
                           LEFT JOIN registration r
                       ON s.sessionID = r.sessionID
                       GROUP BY s.sessionID
                       ORDER BY count DESC
                           LIMIT 1
                       """)
        pop_session = cursor.fetchone()

        # 3. Get Company with most attendees
        cursor.execute("""
                       SELECT c.companyName, COUNT(a.attendeeID) as count
                       FROM company c
                           JOIN attendee a
                       ON c.companyID = a.attendeeCompanyID
                       GROUP BY c.companyID
                       ORDER BY count DESC
                           LIMIT 1
                       """)
        top_company = cursor.fetchone()

        # Displaying with Rich Panel for visual appeal
        dashboard_text = (
            f"[bold cyan]Total Attendees:[/bold cyan] {total_attendees}\n"
            f"[bold cyan]Top Session:[/bold cyan] {pop_session[0] if pop_session else 'N/A'} ({pop_session[1] if pop_session else 0} registrations)\n"
            f"[bold cyan]Top Company:[/bold cyan] {top_company[0] if top_company else 'N/A'} ({top_company[1] if top_company else 0} attendees)"
        )

        console.print(
            Panel(dashboard_text, title="[bold yellow]Conference Insights Dashboard[/bold yellow]", expand=False))
        input("\nPress Enter to return to menu...")

    except Error as e:
        print(f"Error generating dashboard: {e}")


# ===============================
# NEW: TUI MENU DISPLAY
# ===============================

def display_menu():
    """Renders a beautiful menu table using Rich."""
    table = Table(title="Conference Management System", title_style="bold magenta", header_style="bold yellow",
                  border_style="cyan")

    table.add_column("Option", justify="center")
    table.add_column("Functionality", justify="left")

    table.add_row("1", "View Speakers and Sessions")
    table.add_row("2", "View Attendees by Company")
    table.add_row("3", "Add New Attendee")
    table.add_row("4", "View Connected Attendees")
    table.add_row("5", "Add Attendee Connection")
    table.add_row("6", "View Rooms")
    table.add_row("7", "[bold green]View Conference Dashboard[/bold green]")
    table.add_row("x", "[bold red]Exit Application[/bold red]")

    console.print(Panel(table, border_style="cyan", title="[bold white]EVENT MANAGER v2.0[/bold white]"))

# ==========================================
# THE MAIN FUNCTION TO RUN THE APPLICATION
# ==========================================
# variables are initialized to "None", in case connection could not be established, to prevent program from crashing
def main():
    conn, mysql_cursor, neo4j_driver = None, None, None
    try:
        # Standard connections
        conn = mysql.connector.connect(host=cfg.mysql['host'], user=cfg.mysql['user'],
                                       password=cfg.mysql['password'], database=cfg.mysql['database'])
        mysql_cursor = conn.cursor()
        neo4j_driver = GraphDatabase.driver(cfg.neo4j['uri'], auth=(cfg.neo4j['username'], cfg.neo4j['password']))
        room_cache = []

        while True:
            # Display the TUI menu
            display_menu()

            choice = input("Select an option: ").strip().lower()

            if choice == '1':
                view_speakers_and_sessions(mysql_cursor)
            elif choice == '2':
                view_attendees_by_company(mysql_cursor)
            elif choice == '3':
                add_new_attendee(conn, mysql_cursor)
            elif choice == '4':
                view_connected_attendees(mysql_cursor, neo4j_driver)
            elif choice == '5':
                add_attendee_connection(mysql_cursor, neo4j_driver)
            elif choice == '6':
                view_rooms(mysql_cursor, room_cache)
            elif choice == '7':
                view_conference_dashboard(mysql_cursor)
            elif choice == 'x':
                console.print("[italic yellow]Exiting... Goodbye![/italic yellow]")
                break
            else:
                console.print("[bold red]Invalid choice. Please pick a number from the table.[/bold red]")

    except Error as e:
        console.print(f"[bold red]Connection Error: {e}[/bold red]")
    finally:
        if mysql_cursor: mysql_cursor.close()
        if conn and conn.is_connected(): conn.close()
        if neo4j_driver: neo4j_driver.close()


if __name__ == "__main__":
    main()