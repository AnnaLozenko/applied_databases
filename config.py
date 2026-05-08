import os
from dotenv import load_dotenv
# load credentials from .env into the system
load_dotenv(override=True)

mysql = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE', 'app_db')
}

neo4j = {
    'uri' : os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'username' : os.getenv('NEO4J_USER', 'neo4j'),
    'password' : os.getenv('NEO4J_PASSWORD')
}
