### Prerequisites

- Python 3.11.9
- pip

### Installation

    To install the dependencies, run:
    pip install -r requirements.txt

### Running the Program

    To start the program, run:
    python main.py

### Expected Output
    After running python main.py:

    - A window will appear with a grid showing the Wumpus World Game with the agent at (0, 0)
    - Start and Pause buttons to start/pause the agent's exploration process
    - Restart button to get a new map with current settings
    - The user can also create a new map with different settings
    - Status messages will appear in the terminal after pressing Start

### Project Structure
    └── /
        ├── advanced_planning.py
        ├── agent.py
        ├── environment.py
        ├── images
        │   ├── agent.png
        │   ├── arrow.png
        │   ├── breeze.png
        │   ├── pit.png
        │   ├── shot.png
        │   ├── stench.png
        │   ├── treasure.png
        │   └── wumpus.png
        ├── inference.py
        ├── main.py
        ├── planning.py
        ├── readme.md
        ├── requirements.txt
        └── visualizer.py
