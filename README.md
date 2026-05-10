# Applied Databases Final Project
## Conference Management System (v2.0)

### Description
A robust, hybrid database application designed to manage conference logistics, attendee registrations, and social networking. This project integrates Relational (MySQL) and Graph (Neo4j) databases to provide a comprehensive management solution.

<p>
  <img src="event%20manager.png" width="800" alt="Event Manager App">
</p>


Key features include:
- **Speaker & Session Tracking:** Search and display conference schedules and room assignments.  
- **Company Management:** Generate detailed reports of attendees grouped by their organizations.
- **Attendee Registration:** A secure, validated system to add new participants with database integrity checks.
- **Social Networking:** Map and manage professional connections between attendees using Neo4J graph database.
- **Performance Caching:** Optimized room lookup using in-memory caching to reduce database load.
- **Visualization:** Informative conference insights dashboard. 

### Directory Map

```
.
├── main.py                 # Main application entry point
├── .gitignore              # Files to exclude from Git
├── README.md               # Project overview and documentation
├── requirements.txt        # List of necessary Python dependencies
├── config.py               # Configuration file for database credentials (using environment variables)
├── .env.example            # Example .env file for environment variable setup
├── db/
│   ├── init_mysql.sql      # Database schema and seed data
│   └── init_neo4j.cypher   # Graph constraints and initial nodes


```
### Innovations and Enhancements
1. **Advanced Terminal User Interface (TUI):** Leveraging the ```rich``` library for enhanced terminal output, providing a more engaging user experience.
2. **Business Intelligence Dashboard:** A visual dashboard to display real-time key conference metrics and insights.
3. **Optimized User Experience (UX):** Implemented a non-linear navigation flow, allowing users to use the universal "x" command to return to the main menu from any point in the application. Implemented a robust input validation and ensured live data refreshing after any database updates, enhancing the overall user experience and data integrity.

### Technologies Used

- **MySQL:** For structured data management of attendees, sessions, and companies.
- **Neo4j:** For managing and visualizing relationships between attendees.
- **Python 3.12:** For backend logic, database interactions, and caching mechanisms.
- **UI Framework:** ```rich``` for a user-friendly interface (terminal formatting).

### Setup Instructions
1. Clone the repository:
```bash
git clone https://github.com/AnnaLozenko/applied_databases.git

```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Environment Configuration: To follow industry security best practices, this application does not contain hardcoded credentials. It utilizes environment variables.
- Create a file named ```.env``` in the root directory.

- Copy the template below into your new ```.env``` file and replace the placeholders with your actual credentials.  

```env
# MySQL Database Credentials
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASS=mysql_password
MYSQL_DB=conference_db

# Neo4j Database Credentials
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=neo4j_password
```

3. Database Initialization: Run the provided ```db/init_mysql.sql``` in MySQL Workbench and the ```db/init_neo4j.cypher``` in the Neo4j Browser to automatically set up the required tables, constraints, and sample data.
- Ensure MySQL server is running with the provided ```.sql``` schema.
- Ensure Neo4j is active and the URI/Credentials match those in the ```.env``` file.
4. Run the application:
```bash
python main.py
```
