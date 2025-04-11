from flask import Flask, render_template, request, jsonify
import pandas as pd
from difflib import get_close_matches

app = Flask(__name__)

class RITBusChatbot:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.df['Route Name'] = self.df['Route Name'].str.upper()
        self.df['Boarding Points'] = self.df['Boarding Points'].str.upper()
        
    def find_route_by_number(self, route_number):
        route = self.df[self.df['Route Number'].str.upper() == route_number.upper()]
        if not route.empty:
            return route.iloc[0]
        return None
    
    def find_route_by_name(self, route_name):
        # Try exact match first
        route = self.df[self.df['Route Name'] == route_name.upper()]
        if not route.empty:
            return route.iloc[0]
        
        # Try fuzzy matching if no exact match
        all_routes = self.df['Route Name'].unique()
        matches = get_close_matches(route_name.upper(), all_routes, n=1, cutoff=0.6)
        if matches:
            route = self.df[self.df['Route Name'] == matches[0]]
            return route.iloc[0]
        return None
    
    def find_routes_by_boarding_point(self, point):
        point = point.upper()
        routes = []
        for _, row in self.df.iterrows():
            if point in row['Boarding Points']:
                routes.append(row)
        return routes
    
    def get_all_routes(self):
        return self.df
    
    def format_route_info(self, route):
        if isinstance(route, pd.Series):
            return (
                f"Route {route['Route Number']} - {route['Route Name'].title()}\n"
                f"Starting Time: {route['Starting Time']}\n"
                f"Boarding Points:\n{route['Boarding Points'].title()}"
            )
        return "Route information not found."
    
    def respond_to_query(self, query):
        query = query.upper().strip()
        
        # Check for route number queries (R-1, R1, etc.)
        if query.startswith('R-') or query.startswith('R '):
            route = self.find_route_by_number(query)
            if route is not None:
                return self.format_route_info(route)
        
        # Check if query is a route name
        route = self.find_route_by_name(query)
        if route is not None:
            return self.format_route_info(route)
        
        # Check if query is a boarding point
        routes = self.find_routes_by_boarding_point(query)
        if routes:
            if len(routes) == 1:
                return f"Found 1 route for {query.title()}:\n\n" + self.format_route_info(routes[0])
            else:
                response = f"Found {len(routes)} routes for {query.title()}:\n\n"
                for route in routes:
                    response += f"{route['Route Number']} - {route['Route Name'].title()}\n"
                    response += f"Starting Time: {route['Starting Time']}\n\n"
                return response.strip()
        
        # Check for general requests
        if "ALL ROUTES" in query or "LIST ROUTES" in query:
            all_routes = self.get_all_routes()
            response = "All RIT Bus Routes:\n\n"
            for _, route in all_routes.iterrows():
                response += f"{route['Route Number']} - {route['Route Name'].title()}\n"
            return response.strip()
        
        if "HELP" in query or "SUPPORT" in query:
            return (
                "I can help you with RIT bus route information. You can ask me about:\n"
                "- Specific routes by number (e.g., 'R-1' or 'R1')\n"
                "- Routes by name (e.g., 'Ennore' or 'Triplicane')\n"
                "- Routes serving a particular boarding point (e.g., 'Central' or 'Egmore')\n"
                "- List all routes by saying 'all routes'\n"
                "- Bus timings for any route"
            )
        
        return "I couldn't find information for your query. Try asking about a specific route number, route name, or boarding point. Type 'help' for assistance."

# Initialize the chatbot with the CSV file
chatbot = RITBusChatbot("rit_bus_routes.csv")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data['query']
    response = chatbot.respond_to_query(query)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)