"""CSC111 Assignment 1: Text Adventure Game - Simulator

Instructions (READ THIS FIRST!)
===============================

This Python module contains code for Assignment 1 that allows a user to simulate the
playthrough of the game. Please consult the handout for instructions and details.

Do NOT modify any function/method headers, type contracts, etc. in this class (similar
to CSC110 assignments).

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Optional

from event_logger import Event, EventList


# Note: We have completed the Location class for you. Do NOT modify it here for A1.
@dataclass
class Location:
    """
    A location in our text adventure game world.

    Instance Attributes:
        - id_num: integer id for this location
        - description: Long description of this location
        - available_commands: a mapping of available commands at this location to
                                the location executing that command would lead to
    """
    id_num: int
    description: str
    available_commands: dict[str, int]


class SimpleAdventureGame:
    """
    A simple text adventure game class storing all location data.

    Instance Attributes:
        - current_location_id: the ID of the location the game is currently in
    """
    # Private Instance Attributes:
    #   - _locations: a mapping from location id to Location object. This represents all the locations in the game.
    current_location_id: int
    _locations: dict[int, Location]

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file.

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """
        # Note: We have completed this method for you. Do NOT modify it here for A1.

        self._locations = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id  # game begins at this location

    @staticmethod
    def _load_game_data(filename: str) -> dict[int, Location]:
        """
        Load locations from a JSON file with the given filename and
        return a dictionary of locations mapping each game location's ID to a Location object.
        """
        # Note: We have completed this method for you. Do NOT modify it here for A1.

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['id'], loc_data['long_description'], loc_data['available_commands'])
            locations[loc_data['id']] = location_obj

        return locations

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """
        Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough.
    """
    # Private Instance Attributes:
    #   - _game: The AdventureGame instance that this simulation uses.
    #   - _events: A collection of the events to process during the simulation.
    _game: SimpleAdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        """
        Initialize a new game simulation based on the given game data, that runs through the given commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from the location at initial_location_id
        """
        self._events = EventList()
        self._game = SimpleAdventureGame(game_data_file, initial_location_id)

        # Hint: self._game.get_location() gives you back the current location
        start_loc = self._game.get_location()
        first_event = Event(start_loc.id_num, start_loc.description)
        self._events.add_event(first_event, None)

        # Hint: Call self.generate_events with the appropriate arguments
        self.generate_events(commands, start_loc)

    def generate_events(self, commands: list[str], current_location: Location) -> None:
        """
        Generate events in this simulation, based on current_location and commands, a valid list of commands.

        Preconditions:
        - len(commands) > 0
        - all commands in the given list are valid commands when starting from current_location
        """
        # Hint: current_location.available_commands[command] will return the next location ID resulting from executing
        # <command> while in <current_location_id>
        for command in commands:
            next_loc_id = current_location.available_commands[command]
            next_loc = self._game.get_location(next_loc_id)
            new_event = Event(next_loc.id_num, next_loc.description)
            self._events.add_event(new_event, command)
            current_location = next_loc

    def get_id_log(self) -> list[int]:
        """
        Get back a list of all location IDs in the order that they are visited within a game simulation
        that follows the given commands.

        >>> sim = AdventureGameSimulation('sample_locations.json', 1, ["go east"])
        >>> sim.get_id_log()
        [1, 2]

        >>> sim = AdventureGameSimulation('sample_locations.json', 1, ["go east", "go east", "buy coffee"])
        >>> sim.get_id_log()
        [1, 2, 3, 3]
        """
        # Note: We have completed this method for you. Do NOT modify it for A1.

        return self._events.get_id_log()

    def run(self) -> None:
        """
        Run the game simulation and print location descriptions.
        """
        # Note: We have completed this method for you. Do NOT modify it for A1.

        current_event = self._events.first  # Start from the first event in the list

        while current_event:
            print(current_event.description)
            if current_event is not self._events.last:
                print("You choose:", current_event.next_command)

            # Move to the next event in the linked list
            current_event = current_event.next


if __name__ == "__main__":
    # pass
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['json', 'event_logger'],
        'allowed-io': ['AdventureGameSimulation.run', 'SimpleAdventureGame._load_game_data'],
        'disable': ['R1705', 'static_type_checker']
    })
