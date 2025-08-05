import os
import requests
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

API_KEY = os.getenv("DV_API_KEY")
DATABASE_API_URL = "https://c3ntrala.ag3nts.org/apidb"
CENTRAL_API_URL = "https://c3ntrala.ag3nts.org/report"

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")

def query_database(sql_query: str) -> Dict[str, Any]:
    """Executes SQL query to database via API"""
    payload = {
        "task": "database",
        "apikey": API_KEY,
        "query": sql_query
    }
    
    response = requests.post(DATABASE_API_URL, json=payload)
    print(f"Database API Response: {response.status_code}")
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Database API error: {response.status_code} - {response.text}")

def get_users_data() -> List[Dict[str, Any]]:
    """Fetches users data from MySQL database"""
    print("Fetching users data...")
    result = query_database("SELECT id, username FROM users;")
    
    if 'reply' in result:
        return result['reply']
    elif 'data' in result:
        return result['data']
    else:
        return result

def get_connections_data() -> List[Dict[str, Any]]:
    """Fetches connections data from MySQL database"""
    print("Fetching connections data...")
    result = query_database("SELECT * FROM connections;")
    
    if 'reply' in result:
        return result['reply']
    elif 'data' in result:
        return result['data']
    else:
        return result

class Neo4jGraph:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self) -> None:
        self.driver.close()
    
    def clear_database(self) -> None:
        """Clears all data from the database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("Database cleared")
    
    def create_users(self, users: List[Dict[str, Any]]) -> None:
        """Creates user nodes in Neo4j"""
        with self.driver.session() as session:
            for user in users:
                session.run(
                    "CREATE (u:User {userId: $userId, username: $username})",
                    userId=user['id'], username=user['username']
                )
        print(f"Created {len(users)} user nodes")
    
    def create_connections(self, connections: List[Dict[str, Any]]) -> None:
        """Creates connection relationships in Neo4j"""
        with self.driver.session() as session:
            for connection in connections:
                # Assuming connections table has user1_id and user2_id columns
                # Adjust column names based on actual database structure
                user1_id = connection.get('user1_id') or connection.get('user_id_1') or connection.get('user1')
                user2_id = connection.get('user2_id') or connection.get('user_id_2') or connection.get('user2')
                
                if user1_id and user2_id:
                    session.run(
                        """
                        MATCH (u1:User {userId: $user1_id})
                        MATCH (u2:User {userId: $user2_id})
                        CREATE (u1)-[:KNOWS]->(u2)
                        """,
                        user1_id=user1_id, user2_id=user2_id
                    )
        print(f"Created {len(connections)} connection relationships")
    
    def find_shortest_path(self, start_name: str, end_name: str) -> Optional[List[str]]:
        """Finds shortest path between two users by name"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = shortestPath(
                    (start:User {username: $start_name})-[*]-(end:User {username: $end_name})
                )
                RETURN [node in nodes(path) | node.username] as path_names
                """,
                start_name=start_name, end_name=end_name
            )
            
            record = result.single()
            if record:
                return record["path_names"]
            return None

def main() -> None:
    """Main function executing the task"""
    try:
        # Step 1: Fetch data from MySQL
        print("Step 1: Fetching data from MySQL...")
        users = get_users_data()
        connections = get_connections_data()
        
        print(f"Found {len(users)} users and {len(connections)} connections")
        
        # Step 2: Connect to Neo4j
        print("Step 2: Connecting to Neo4j...")
        graph = Neo4jGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Step 3: Clear database and load data
        print("Step 3: Loading data into Neo4j...")
        graph.clear_database()
        graph.create_users(users)
        graph.create_connections(connections)
        
        # Step 4: Find shortest path
        print("Step 4: Finding shortest path...")
        path = graph.find_shortest_path("Rafał", "Barbara")
        
        if path:
            print(f"Found path: {path}")
            answer = ",".join(path)
        else:
            print("No path found between Rafał and Barbara")
            answer = ""
        
        # Step 5: Submit answer
        print("Step 5: Submitting answer...")
        payload = {
            "task": "connections",
            "apikey": API_KEY,
            "answer": answer
        }
        
        response = requests.post(CENTRAL_API_URL, json=payload)
        print(f"Central API Response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print("Answer submitted successfully!")
        else:
            print(f"Error submitting answer: {response.status_code}")
        
        # Cleanup
        graph.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 