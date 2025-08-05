import os
import requests
from typing import List, Dict, Any, Optional
import networkx as nx
import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

API_KEY = os.getenv("DV_API_KEY")
DATABASE_API_URL = "https://c3ntrala.ag3nts.org/apidb"
CENTRAL_API_URL = "https://c3ntrala.ag3nts.org/report"

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

class NetworkXGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.user_id_to_name = {}
        self.user_name_to_id = {}
    
    def build_graph(self, users: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> None:
        """Builds the graph from users and connections data"""
        print("Building graph from data...")
        
        # Create user mapping
        for user in users:
            user_id = user['id']
            username = user['username']
            self.user_id_to_name[user_id] = username
            self.user_name_to_id[username] = user_id
            self.graph.add_node(username)
        
        # Add connections
        for connection in connections:
            # Try different possible column names
            user1_id = connection.get('user1_id') or connection.get('user_id_1') or connection.get('user1')
            user2_id = connection.get('user2_id') or connection.get('user_id_2') or connection.get('user2')
            
            if user1_id and user2_id and user1_id in self.user_id_to_name and user2_id in self.user_id_to_name:
                user1_name = self.user_id_to_name[user1_id]
                user2_name = self.user_id_to_name[user2_id]
                self.graph.add_edge(user1_name, user2_name)
        
        print(f"Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def find_shortest_path(self, start_name: str, end_name: str) -> Optional[List[str]]:
        """Finds shortest path between two users by name"""
        try:
            if start_name not in self.graph or end_name not in self.graph:
                print(f"One or both users not found: {start_name}, {end_name}")
                return None
            
            path = nx.shortest_path(self.graph, start_name, end_name)
            return path
        except nx.NetworkXNoPath:
            print(f"No path found between {start_name} and {end_name}")
            return None
    
    def print_graph_info(self) -> None:
        """Prints information about the graph"""
        print(f"Graph has {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        print(f"Connected components: {nx.number_connected_components(self.graph)}")
        
        # Check if Rafał and Barbara are in the same component
        if "Rafał" in self.graph and "Barbara" in self.graph:
            rafal_component = nx.node_connected_component(self.graph, "Rafał")
            barbara_component = nx.node_connected_component(self.graph, "Barbara")
            if rafal_component == barbara_component:
                print("Rafał and Barbara are in the same connected component")
            else:
                print("Rafał and Barbara are in different connected components - no path exists")

def main() -> None:
    """Main function executing the task"""
    try:
        # Step 1: Fetch data from MySQL
        print("Step 1: Fetching data from MySQL...")
        users = get_users_data()
        connections = get_connections_data()
        
        print(f"Found {len(users)} users and {len(connections)} connections")
        
        # Step 2: Build graph
        print("Step 2: Building graph...")
        graph = NetworkXGraph()
        graph.build_graph(users, connections)
        graph.print_graph_info()
        
        # Step 3: Find shortest path
        print("Step 3: Finding shortest path...")
        path = graph.find_shortest_path("Rafał", "Barbara")
        
        if path:
            print(f"Found path: {path}")
            answer = ",".join(path)
        else:
            print("No path found between Rafał and Barbara")
            answer = ""
        
        # Step 4: Submit answer
        print("Step 4: Submitting answer...")
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
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 