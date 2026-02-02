"""CSC111 Project 1: Text Adventure Game - Game Manager

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

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
from typing import Optional

from game_entities import Location, Item
from event_logger import Event, EventList


# Note: You may add in other import statements here as needed

# Note: You may add helper functions, classes, etc. below as needed


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - current_location_id: the ID of player's current location
        - ongoing:

    Representation Invariants:

    """

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a list of Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: list[Item]
    current_location_id: int  # Suggested attribute, can be removed
    ongoing: bool  # Suggested attribute, can be removed

    # Game state attributes (baseline requirements)
    event_log: EventList
    inventory: list[Item]
    score: int
    moves_used: int
    max_moves: int

    def __init__(self, game_data_file: str, initial_location_id: int, max_moves: int = 30) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        (note: you are allowed to modify the format of the file as you see fit)

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """

        # NOTES:
        # You may add parameters/attributes/methods to this class as you see fit.

        # Requirements:
        # 1. Make sure the Location class is used to represent each location.
        # 2. Make sure the Item class is used to represent each item.

        # Suggested helper method (you can remove and load these differently if you wish to do so):
        self._locations, self._items = self._load_game_data(game_data_file)

        # Suggested attributes (you can remove and track these differently if you wish to do so):
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing

        self.event_log = EventList()
        self.inventory = []
        self.score = 0
        self.moves_used = 0
        self.max_moves = max_moves

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['id'], loc_data['brief_description'], loc_data['long_description'],
                                    loc_data['available_commands'], loc_data['items'])
            locations[loc_data['id']] = location_obj

        items = []
        # TODO: Add Item objects to the items list; your code should be structured similarly to the loop above
        # YOUR CODE BELOW
        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['start_position'], item_data['target_position'],
                            item_data['target_points'])
            items.append(item_obj)

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """

        # TODO: Complete this method as specified
        # YOUR CODE BELOW
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_item_by_names(self, name: str) -> Optional[Item]:
        """Return the Item whose name matches. Otherwise, return None"""
        name = name.strip().lower()
        for i in self._items:
            if i.name.strip().lower() == name:
                return i
        return None

    def show_inventory(self):
        """Return a list of items in player's inventory"""
        return [item.name for item in self.inventory]

    def consume_moves(self):
        """Increase the player's move by 1 and check if it reaches the maxmimum moves allowed"""
        self.moves_used += 1
        if self.moves_used >= self.max_moves:
            self.ongoing = False
            return f"You ran out of moves. YOU LOSE :(( (moves: {self.moves_used}/{self.max_moves})"
        return None

    def _current_location(self) -> Location:
        """Return the player's current Location object."""
        return self._locations[self.current_location_id]

    def _find_item(self, item_name: str) -> Optional[Item]:
        """Return the Item object whose name matches item_name (case-insensitive), or None."""
        name = item_name.strip().lower()
        for item in self._items:
            if item.name.lower() == name:
                return item
        return None

    def process_choice(self, command: str):
        """Process the player's command"""

        command = command.strip().lower()
        loc = self.get_location()

        if command == "":
            return "Please enter a command."

        # --- Quit ---
        if command == "quit":
            self.ongoing = False
            return "You quit the game."

        # --- Look ---
        if command == "look":
            return self.describe_current_location(force_long=True)

        # --- Inventory ---
        if command == "inventory":
            if not self.inventory:
                return "Inventory: (empty)"
            return "Inventory: " + ", ".join(self._inventory_names())

        # --- Score ---
        if command == "score":
            return f"Score: {self.score} | Moves: {self.moves_used}/{self.max_moves}"

        # --- Log ---
        if command == "log":
            self.event_log.display_events()
            return ""

    def take(self, item: str) -> str:
        """Take the item from current location into inventory (Case - sensitive)
        Add 1 point as a reward"""

        if item == "":
            return "Take what?"

        loc = self._current_location()

        match = None
        for name in loc.items:
            if name.lower() == item.lower():
                match = name
                break

        match = None
        for name in loc.items:
            if name.lower() == item.lower():
                match = name
                break
        if match is None:
            return f"There is no '{item}' here to take."

        item_obj = self._find_item(match)
        if item_obj is None:
            return f"That item '{match}' isn't in the items list."

        loc.items.remove(match)
        self.inventory.append(item_obj)

        self.consume_moves()
        self.score += 1  # small reward for picking up

        self.event_log.add_event(Event(loc.id_num, loc.brief_description), f"take {item_obj.name}")

        end_msg = self.win_lose_conditions()
        if end_msg:
            return end_msg
        else:
            return f"Taken"

    def drop(self, item_name: str) -> str:
        """Drop the item in the inventory to current location
        Increase the point when the item is return to its target location
        """
        if item_name == "":
            return f"Drop what?"

        loc = self._current_location()

        # Find item in inventory (case-insensitive)
        idx = None
        for i, item in enumerate(self.inventory):
            if item.name.lower() == item_name.lower():
                idx = i
                break
        if idx is None:
            return f"You aren't carrying '{item_name}'."

        item_obj = self.inventory.pop(idx)
        loc = self._current_location()
        loc.items.append(item_obj.name)

        self._consume_move()

        # Deposit scoring
        if loc.id_num == item_obj.target_position:
            self.score += item_obj.target_points

        self.event_log.add_event(Event(loc.id_num, loc.brief_description), f"drop {item_obj.name}")

        end_msg = self._check_end_conditions()
        return end_msg if end_msg else f"You dropped: {item_obj.name}"
    def win_lose_conditions(self) -> str:
        """Return a message if the game end. Otherwise, return an empty stirng"""
        # Lose condition: The player runs out of moves
        if not self.ongoing and self.moves_used >= self.max_moves:
            return f"You ran out of moves (moves used: {self.moves_used}). It's 1pm — you lose."

        # Win condition: All items are in their target positions (not in inventory)
        if self.ongoing:
            all_delivered = True
            for item in self._items:
                # If still in inventory, not delivered
                if any(inv_item.name.lower() == item.name.lower() for inv_item in self.inventory):
                    all_delivered = False
                    break
                # Must be present at target location
                target_loc = self._locations.get(item.target_position)
                if target_loc is None or item.name not in target_loc.items:
                    all_delivered = False
                    break

            if all_delivered:
                self.ongoing = False
                return "You returned all the missing items. CONGRATULATIONS! YOU WIN :))"

        return ""




if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })
    game = AdventureGame('game_data.json', 1)  # load data, setting initial location ID to 1
    menu = ["look", "inventory", "score", "log", "quit"]  # Regular menu options available at each location
    choice = None

    # Note: You may modify the code below as needed; the following starter code is just a suggestion
    while game.ongoing:
        # Note: If the loop body is getting too long, you should split the body up into helper functions
        # for better organization. Part of your mark will be based on how well-organized your code is.

        location = game.get_location()

        # TODO: Add new Event to game log to represent current game location
        #  Note that the <choice> variable should be the command which led to this event
        # Add an Event for entering this location (only if it is the first event OR location changed)
        if game.event_log.is_empty() or (game.event_log.last is not None and game.event_log.last.id_num != location.id_num):
            new_event = Event(location.id_num, location.long_description)
            game.event_log.add_event(new_event, choice)


        # TODO: Depending on whether or not it's been visited before,
        #  print either full description (first time visit) or brief description (every subsequent visit) of location
        if location.visited:
            print(location.brief_description)
        else:
            print(location.long_description)
            location.visited = True

        # Display possible actions at this location
        print("What to do? Choose from: look, inventory, score, log, quit")
        if location.available_commands:
            print("From here, you can also:")
            for action in location.available_commands:
                print("-", action)

        # Validate choice
        choice = input("\nEnter action: ").lower().strip()
        while choice not in location.available_commands and choice not in menu:
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)


            # TODO: Add in code to deal with actions which do not change the location (e.g. taking or using an item)
            # TODO: Add in code to deal with special locations (e.g. puzzles) as needed for your game
