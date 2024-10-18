import asyncio
import websockets
import json
from dash import Dash, dcc, html, Input, Output
import dash_table

# Initialize the Dash app
app = Dash(__name__)

# Global variable to hold data for multiple sessions
sessions_data = {}
current_session = None  # To store the current session ID

# Define the layout of the Dash app
app.layout = html.Div([
    html.H1("Prison-Dilemma Score Board"),
    dcc.Dropdown(
        id='session-dropdown',
        options=[],
        value=None,
        placeholder="Select a session",
        clearable=False
    ),
    dash_table.DataTable(
        id='data-table',
        columns=[
            {"name": "Player ID", "id": "player_id"},
            {"name": "Strategy", "id": "move"},
            {"name": "Score", "id": "score"},
            {"name": "Round", "id": "round"}
        ],
        data=[],
        page_size=10,
    ),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # Update every second
        n_intervals=0
    )
])

async def websocket_connect(player_id):
    uri = "ws://localhost:6789"
    async with websockets.connect(uri, timeout=20) as websocket:
        await websocket.send(player_id)

        while True:
            result = await websocket.recv()
            result_data = json.loads(result)

            # Check if session ID is in the received data
            if 'Session_id' in result_data:
                global current_session
                current_session = result_data['Session_id']

                # Add session to dropdown options if it doesn't already exist
                dropdown_options = app.layout.children[1].options  # Access dropdown by index
                if not any(option['value'] == current_session for option in dropdown_options):
                    dropdown_options.append({'label': current_session, 'value': current_session})
            # Update global data variable with new data
            update_data(result_data)

def update_data(result_data):
    global sessions_data
    
    # Extract relevant information from result_data
    player1_id = result_data['Team1']['player_id']
    player1_move = result_data['Team1']['move']
    player1_score = result_data['Team1']['score']
    round_num = result_data['Team1']['round']
    session_id = result_data.get('Session_id', current_session)  # Use current_session if not provided

    player2_id = result_data['Team2']['player_id']
    player2_move = result_data['Team2']['move']
    player2_score = result_data['Team2']['score']

    # Initialize session data if it doesn't exist
    if session_id not in sessions_data:
        sessions_data[session_id] = []

    # Append new data for both teams in the current session
    sessions_data[session_id].append({
        "player_id": player1_id,
        "move": player1_move,
        "score": player1_score,
        "round": round_num
    })
    
    sessions_data[session_id].append({
        "player_id": player2_id,
        "move": player2_move,
        "score": player2_score,
        "round": round_num
    })

@app.callback(
    Output('data-table', 'data'),
    Input('interval-component', 'n_intervals'),
    Input('session-dropdown', 'value')
)
def update_table(n, selected_session):
    global current_session
    
    if selected_session is not None:
        current_session = selected_session
    
    # Return data for the selected session or an empty list if no session exists
    return sessions_data.get(current_session, [])

# Run the WebSocket connection in a separate thread
def run_websocket():
    asyncio.run(websocket_connect("Visualizer"))

if __name__ == '__main__':
    import threading
    
    # Start WebSocket client in a separate thread
    ws_thread = threading.Thread(target=run_websocket)
    ws_thread.start()

    # Run the Dash app
    app.run_server(debug=True)