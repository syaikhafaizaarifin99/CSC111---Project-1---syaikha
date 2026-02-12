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
import random
from dataclasses import dataclass
from typing import Optional, Tuple

from game_entities import Location, Item
from event_logger import Event, EventList

# Note: You may add in other import statements here as needed

# Note: You may add helper functions, classes, etc. below as needed


# -------------------------
# Evolution Arena constants
# -------------------------
TYPES: tuple[str, ...] = ("rock", "paper", "scissors", "shadow")

DOMINANCE: dict[str, set[str]] = {
    "rock": {"scissors"},
    "paper": {"rock"},
    "scissors": {"paper"},
    "shadow": set(),  # special rule handled separately
}

ARENA_START_ENERGY = 3
ARENA_WIN_POINTS = 1
ARENA_TARGET_POINTS = 5


# -------------------------
# Undo + Arena gating state
# -------------------------
@dataclass
class GameSnapshot:
    """A snapshot of the game state, used for the undo feature."""
    current_location_id: int
    moves_used: int
    score: int
    inventory_names: list[str]
    location_items: dict[int, list[str]]
    visited: dict[int, bool]
    event_log_data: list[tuple[int, str, str]]
    bahen_arena_won: bool


# -------------------------
# Evolution Arena classes
# (User requested Move stays in this file)
# -------------------------
@dataclass(frozen=True)
class Move:
    type: str
    power: int  # 1..3

    def __post_init__(self) -> None:
        if self.type not in TYPES:
            raise ValueError(f"Invalid type: {self.type}")
        if not (1 <= self.power <= 3):
            raise ValueError(f"Power must be 1..3, got {self.power}")


@dataclass
class ArenaPlayer:
    """Separate from adventure inventory Player; used only inside the Arena mini-game."""
    name: str
    energy: int = ARENA_START_ENERGY
    points: int = 0
    last_move: Optional[Move] = None


# -------------------------
# Evolution Arena helpers
# -------------------------
def arena_energy_cost(move: Move) -> int:
    base = 0
    if move.power == 2:
        base = 1
    elif move.power == 3:
        base = 2
    if move.type == "shadow":
        base += 2
    return base


def arena_beats(a: Move, b: Move) -> bool:
    """Return True iff a beats b by dominance rules."""
    if a.type == "shadow" and b.power == 1:
        return True
    return b.type in DOMINANCE[a.type]


def arena_resolve_round(p1: ArenaPlayer, m1: Move, p2: ArenaPlayer, m2: Move) -> Tuple[int, int, str]:
    """Return (p1_points_gained, p2_points_gained, outcome_text)."""
    p1_dom = arena_beats(m1, m2)
    p2_dom = arena_beats(m2, m1)

    if p1_dom and not p2_dom:
        return (ARENA_WIN_POINTS, 0, f"{p1.name} wins (type advantage).")
    if p2_dom and not p1_dom:
        return (0, ARENA_WIN_POINTS, f"{p2.name} wins (type advantage).")

    # No clear dominance -> compare power
    if m1.power > m2.power:
        return (ARENA_WIN_POINTS, 0, f"{p1.name} wins (power {m1.power} > {m2.power}).")
    if m2.power > m1.power:
        return (0, ARENA_WIN_POINTS, f"{p2.name} wins (power {m2.power} > {m1.power}).")

    return (0, 0, "Draw (same strength).")


def arena_parse_move(s: str) -> Optional[Move]:
    """
    Accepted formats:
      - "rock 2"
      - "scissors3"
      - "shadow 1"
      - "paper"
    If power omitted, defaults to 1.
    """
    s = s.strip().lower()
    if not s:
        return None

    # Allow "scissors3" style
    for t in TYPES:
        if s.startswith(t):
            rest = s[len(t):].strip()
            if rest == "":
                return Move(t, 1)
            try:
                return Move(t, int(rest))
            except ValueError:
                pass

    parts = s.split()
    if len(parts) == 1 and parts[0] in TYPES:
        return Move(parts[0], 1)
    if len(parts) == 2 and parts[0] in TYPES:
        try:
            return Move(parts[0], int(parts[1]))
        except ValueError:
            return None
    return None


def arena_enforce_energy(player: ArenaPlayer, desired: Move) -> Tuple[Move, str]:
    """If not affordable, force rock 1."""
    cost = arena_energy_cost(desired)
    if cost <= player.energy:
        return desired, ""
    forced = Move("rock", 1)
    return forced, (
        f"{player.name} couldn't afford {desired.type} {desired.power} "
        f"(cost {cost}, energy {player.energy}) -> forced to rock 1."
    )


def arena_ai_choose(ai: ArenaPlayer, opponent: ArenaPlayer) -> Move:
    """
    Simple AI:
    - If opponent is low energy, sometimes play shadow 1 to punish power-1.
    - Otherwise, counter opponent's last move type if possible.
    - Pick power based on energy.
    """
    opp_low = opponent.energy <= 1

    # Shadow ambush
    if opp_low and ai.energy >= 2 and random.random() < 0.45:
        return Move("shadow", 1)

    # Counter last move if known
    if opponent.last_move is not None:
        target_type = opponent.last_move.type
        counters = [t for t in TYPES if target_type in DOMINANCE.get(t, set())]
        if opponent.last_move.power == 1 and ai.energy >= 2:
            counters.append("shadow")
        chosen_type = random.choice(counters) if counters else random.choice(TYPES[:-1])
    else:
        chosen_type = random.choice(TYPES[:-1])

    # Choose power
    if ai.energy >= 2 and random.random() < 0.25:
        power = 3
    elif ai.energy >= 1 and random.random() < 0.45:
        power = 2
    else:
        power = 1

    return Move(chosen_type, power)


def arena_print_rules() -> None:
    print("\n=== Evolution Arena Rules ===")
    print("Types: rock, paper, scissors, shadow")
    print("Dominance: rock>scissors, scissors>paper, paper>rock")
    print("Shadow: beats ANY move with power 1")
    print("Power: 1..3")
    print("Energy start:", ARENA_START_ENERGY)
    print("Costs: p1=0, p2=1, p3=2, shadow adds +2")
    print("Regen: winner +1, loser +2, draw both +1")
    print("Scoring: win +1, first to 5 wins")
    print("Input examples: 'rock 2', 'scissors3', 'shadow 1', 'paper'")
    print("Type 'rules' anytime to reprint rules.")
    print("Type 'quit' anytime to quit the arena.\n")


def arena_prompt_move(player: ArenaPlayer) -> Optional[Move]:
    """Prompt the human player for a move.

    The player may also type 'rules' to reprint the rules, or type 'quit' to exit the arena immediately.

    Return:
        - a Move if the player enters a valid move
        - None if the player types 'quit'
    """
    while True:
        raw = input(
            f"{player.name} (energy={player.energy}, points={player.points}) choose move: "
        ).strip()

        if raw.lower() == "quit":
            return None

        if raw.lower() in {"help", "rules", "?"}:
            arena_print_rules()
            continue

        m = arena_parse_move(raw)
        if m is None:
            print("Invalid move. Try 'rock 2' or 'scissors3'. Type 'rules' to see rules.")
            continue

        actual, note = arena_enforce_energy(player, m)
        if note:
            print(note)
        return actual


def arena_apply_regen(p1: ArenaPlayer, p2: ArenaPlayer, gained1: int, gained2: int) -> None:
    """Apply simplified regen rules."""
    if gained1 > gained2:
        # p1 winner
        p1.energy += 1
        p2.energy += 2
    elif gained2 > gained1:
        # p2 winner
        p2.energy += 1
        p1.energy += 2
    else:
        # draw
        p1.energy += 1
        p2.energy += 1


def play_evolution_arena(
    target_points: int = ARENA_TARGET_POINTS, seed: Optional[int] = None
) -> Optional[bool]:
    """Run the Evolution Arena mini-game.

    The human can type 'quit' at any move prompt to exit the arena early.

    Return:
        - True if the human wins the arena
        - False if the human loses the arena
        - None if the human quits early
    """
    if seed is not None:
        random.seed(seed)

    human = ArenaPlayer(name="You", energy=ARENA_START_ENERGY)
    ai = ArenaPlayer(name="CSSU AI", energy=ARENA_START_ENERGY)

    arena_print_rules()

    round_num = 1
    while human.points < target_points and ai.points < target_points:
        print(f"--- Arena Round {round_num} ---")

        m_h = arena_prompt_move(human)
        if m_h is None:
            print("You quit the arena.\n")
            return None

        desired_ai = arena_ai_choose(ai, human)
        m_a, note_a = arena_enforce_energy(ai, desired_ai)
        if note_a:
            print(note_a)

        # Pay energy
        cost_h = arena_energy_cost(m_h)
        cost_a = arena_energy_cost(m_a)
        human.energy -= cost_h
        ai.energy -= cost_a

        human.last_move = m_h
        ai.last_move = m_a

        print(f"You play:    {m_h.type} {m_h.power} (cost {cost_h})")
        print(f"CSSU AI plays:{m_a.type} {m_a.power} (cost {cost_a})")

        gained_h, gained_a, outcome = arena_resolve_round(human, m_h, ai, m_a)
        print(outcome)

        human.points += gained_h
        ai.points += gained_a

        arena_apply_regen(human, ai, gained_h, gained_a)

        # Clamp non-negative
        human.energy = max(0, human.energy)
        ai.energy = max(0, ai.energy)

        print(f"Score: You {human.points} - {ai.points} CSSU AI")
        print(f"Energy: You {human.energy} | CSSU AI {ai.energy}\n")

        round_num += 1

    winner = "You" if human.points >= target_points else "CSSU AI"
    print(f"=== ARENA OVER: {winner} wins! ===\n")
    return human.points >= target_points





class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - current_location_id: the ID of player's current location
        - ongoing:

    Representation Invariants:

    """

    _locations: dict[int, Location]
    _items: list[Item]
    current_location_id: int
    ongoing: bool

    event_log: EventList
    inventory: list[Item]
    score: int
    moves_used: int
    max_moves: int

    def __init__(self, game_data_file: str, initial_location_id: int, max_moves: int = 30) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        """
        self._locations, self._items = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing

        self.event_log = EventList()
        self.inventory = []
        self.score = 0
        self.moves_used = 0
        self.max_moves = max_moves

        # Undo stack
        self._undo_stack: list[GameSnapshot] = []

        # Restart support: remember the original starting location id
        self._start_location_id = initial_location_id

        # Bahen gate: must beat CSSU AI once before taking laptop at Bahen
        self.bahen_arena_won = False

        # Add initial event to event log (so Log is not empty at the start)
        start_loc = self.get_current_location()
        self.event_log.add_event(Event(start_loc.id_num, start_loc.long_description), "")

        # Save initial snapshot for restart
        self._initial_snapshot: GameSnapshot = self._make_snapshot()

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], list[Item]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        locations = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['id'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                loc_data['items']
            )
            locations[loc_data['id']] = location_obj

        items = []
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points']
            )
            items.append(item_obj)

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_current_location(self) -> Location:
        """Return the player's current Location."""
        return self._locations[self.current_location_id]

    def get_item_by_names(self, name: str) -> Optional[Item]:
        """Return the Item whose name matches. Otherwise, return None."""
        name = name.strip().lower()
        for i in self._items:
            if i.name.strip().lower() == name:
                return i
        return None

    def show_inventory(self) -> list[str]:
        """Return a list of item names in player's inventory."""
        return [item.name for item in self.inventory]

    def consume_moves(self) -> Optional[str]:
        """Increase moves_used by 1. End the game if max_moves reached.
        Return a lose message if the player loses, otherwise return None.
        """
        self.moves_used += 1
        if self.moves_used >= self.max_moves:
            self.ongoing = False
            return f"You ran out of moves. YOU LOSE :(( (moves: {self.moves_used}/{self.max_moves})"
        return None

    def _find_item(self, item_name: str) -> Optional[Item]:
        """Return the Item object whose name matches item_name (case-insensitive), or None."""
        name = item_name.strip().lower()
        for item in self._items:
            if item.name.strip().lower() == name:
                return item
        return None

    def process_choice(self, choice: str) -> str:
        """Process a command that does not require direct menu validation."""
        choice = choice.strip().lower()

        if choice == "quit":
            self.ongoing = False
            return "Thanks for playing!"

        elif choice == "look":
            # Look should show full description even if already visited.
            return self.describe_current_location(force_long=True)

        elif choice == "inventory":
            inv = self.show_inventory()
            return "Inventory: " + (", ".join(inv) if inv else "(empty)")

        elif choice == "score":
            return f"Your score: {self.score}"

        elif choice == "log":
            # EventList.display_events prints and returns None (A1),
            # so use the string-returning helper from event_logger.py.
            return self.event_log.get_events_as_string()

        elif choice == "undo":
            return self.undo()

        elif choice == "restart":
            return self.restart()

        elif choice.startswith("go "):
            return self.go(choice[3:].strip())

        elif choice.startswith("take "):
            return self.take(choice[5:].strip())

        elif choice.startswith("drop "):
            return self.drop(choice[5:].strip())

        else:
            return "Invalid command."

    def take(self, item: str) -> str:
        """Take the item from the current location into inventory (case-insensitive).
        Adds 1 point as a reward.
        """
        item = item.strip()
        if item == "":
            return "Take what?"

        loc = self.get_current_location()

        match = None
        for name in loc.items:
            if name.lower() == item.lower():
                match = name
                break

        if match is None:
            return f"There is no '{item}' here to take."

        # Bahen puzzle gate: must win arena before taking laptop at Bahen (id 1)
        if loc.id_num == 1 and match.strip().lower() == "laptop" and not self.bahen_arena_won:
            print("\nYour friend blocks the laptop.")
            print("\"This is the CSSU AI model. Beat it first!\"\n")

            while True:
                arena_result = play_evolution_arena(target_points=ARENA_TARGET_POINTS)

                if arena_result is None:
                    return "You quit the arena challenge. The laptop remains locked."

                if arena_result:
                    self.bahen_arena_won = True
                    print("You beat the CSSU AI! Your friend cheers and steps aside.\n")
                    break
                else:
                    print("\nYou lost to the CSSU AI.")
                    retry = input(
                        'Type "Try Again" to challenge it again, type "Quit" to quit, or anything else to stop: '
                    ).strip().lower()

                    if retry == "try again":
                        continue
                    if retry == "quit":
                        return "You quit the arena challenge. The laptop remains locked."
                    return "You step back from the challenge. The laptop remains locked."


        item_obj = self._find_item(match)
        if item_obj is None:
            return f"That item '{match}' isn't in the items list."

        # IMPORTANT: push undo BEFORE changing state
        self._push_undo()

        loc.items.remove(match)
        self.inventory.append(item_obj)

        lose_msg = self.consume_moves()
        if lose_msg is not None:
            return lose_msg

        self.score += 1
        self.event_log.add_event(Event(loc.id_num, loc.brief_description), f"take {item_obj.name}")

        end_msg = self.win_lose_conditions()
        return end_msg if end_msg else f"You picked up {item_obj.name}."

    def drop(self, item_name: str) -> str:
        """Drop an item at the current location."""
        item_name = item_name.strip()
        if item_name == "":
            return "Drop what?"

        location = self.get_current_location()

        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                # IMPORTANT: push undo BEFORE changing state
                self._push_undo()

                self.inventory.remove(item)
                location.items.append(item.name)

                lose_msg = self.consume_moves()
                if lose_msg is not None:
                    return lose_msg

                if location.id_num == item.target_position:
                    self.score += item.target_points

                self.event_log.add_event(Event(location.id_num, location.brief_description), f"drop {item.name}")

                win_msg = self.win_lose_conditions()
                if win_msg:
                    return win_msg

                return f"You dropped {item.name}."

        return "That item is not in your inventory."

    def win_lose_conditions(self) -> str:
        """Return a message if the game ends. Otherwise, return an empty string."""
        if not self.ongoing and self.moves_used >= self.max_moves:
            return f"You ran out of moves (moves used: {self.moves_used}). It's 1pm — you lose."

        if self.ongoing:
            inv_names = {inv_item.name.strip().lower() for inv_item in self.inventory}

            for item in self._items:
                item_name = item.name.strip().lower()

                if item_name in inv_names:
                    return ""

                target_loc = self._locations.get(item.target_position)
                if target_loc is None:
                    return ""

                target_items = {nm.strip().lower() for nm in target_loc.items}
                if item_name not in target_items:
                    return ""

            self.ongoing = False
            return "You returned all the missing items. CONGRATULATIONS! YOU WIN :))"

        return ""

    def go(self, direction: str) -> str:
        """Move the player in the given direction if possible."""
        direction = direction.strip().lower()
        location = self.get_current_location()
        cmd = f"go {direction}"

        next_id = location.available_commands.get(cmd)
        if next_id is None:
            return "You can't go that way."

        # IMPORTANT: push undo BEFORE changing state
        self._push_undo()

        self.current_location_id = next_id

        lose_msg = self.consume_moves()
        if lose_msg is not None:
            return lose_msg

        new_loc = self.get_current_location()
        self.event_log.add_event(Event(new_loc.id_num, new_loc.brief_description), cmd)
        return self.describe_current_location(force_long=False)

    def describe_current_location(self, force_long: bool = False) -> str:
        """Return the appropriate description of the current location.
        - If force_long is True OR this is the first visit: show long description.
        - Otherwise: show brief description.
        Always includes 'LOCATION <id>' header.
        """
        loc = self.get_current_location()

        if force_long or not loc.visited:
            loc.visited = True
            return f"LOCATION {loc.id_num}\n{loc.long_description}"
        else:
            return f"LOCATION {loc.id_num}\n{loc.brief_description}"

    # -------------------------
    # Undo helpers
    # -------------------------
    def _make_snapshot(self) -> GameSnapshot:
        """Create a snapshot of the full game state for undo."""
        inv_names = [it.name for it in self.inventory]
        loc_items = {loc_id: list(loc.items) for loc_id, loc in self._locations.items()}
        visited = {loc_id: loc.visited for loc_id, loc in self._locations.items()}
        log_data = self.event_log.to_list()
        return GameSnapshot(
            current_location_id=self.current_location_id,
            moves_used=self.moves_used,
            score=self.score,
            inventory_names=inv_names,
            location_items=loc_items,
            visited=visited,
            event_log_data=log_data,
            bahen_arena_won=self.bahen_arena_won
        )

    def _restore_snapshot(self, snap: GameSnapshot) -> None:
        """Restore game state from snapshot."""
        self.current_location_id = snap.current_location_id
        self.moves_used = snap.moves_used
        self.score = snap.score

        self.ongoing = self.moves_used < self.max_moves

        for loc_id, items_list in snap.location_items.items():
            self._locations[loc_id].items = list(items_list)
        for loc_id, was_visited in snap.visited.items():
            self._locations[loc_id].visited = was_visited

        self.inventory = []
        for name in snap.inventory_names:
            obj = self.get_item_by_names(name)
            if obj is not None:
                self.inventory.append(obj)

        self.event_log.load_from_list(snap.event_log_data)
        self.bahen_arena_won = snap.bahen_arena_won

    def _push_undo(self) -> None:
        """Save current state so we can undo the next action."""
        self._undo_stack.append(self._make_snapshot())

    def undo(self) -> str:
        """Undo the previous action. Can be repeated."""
        if not self._undo_stack:
            return "Nothing to undo."
        snap = self._undo_stack.pop()
        self._restore_snapshot(snap)
        return "Undid the previous action."

    # -------------------------
    # Restart feature
    # -------------------------
    def restart(self) -> str:
        """Restart the game back to the initial state."""
        self._restore_snapshot(self._initial_snapshot)
        self._undo_stack.clear()

        # Rebuild initial snapshot (safe if user restarts multiple times)
        self._initial_snapshot = self._make_snapshot()

        return "Game restarted.\n" + self.describe_current_location(force_long=True)


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })
    game = AdventureGame('game_data.json', 6)  # load data, setting initial location ID to 1
    menu = ["look", "inventory", "score", "log", "undo", "restart", "quit"]  # Regular menu options available at each location
    choice = None

    show_location = True
    while game.ongoing:
        location = game.get_location()

        # NOTE: We add the initial event in __init__ and add "go" events inside AdventureGame.go().
        # Keeping the original auto-add block would cause duplicated events in the log, so it is commented out.

        if show_location:
            print(game.describe_current_location(force_long=False))
            show_location = False

        print("What to do? Choose from: look, inventory, score, log, undo, restart, quit")
        if location.available_commands:
            print("From here, you can also:")
            for action in location.available_commands:
                print("-", action)

        choice = input("\nEnter action: ").lower().strip()

        while (
            choice not in menu
            and not choice.startswith("take ")
            and not choice.startswith("drop ")
            and not choice.startswith("go ")
        ):
            print("That was an invalid option. Please try again. :((( ")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        result = game.process_choice(choice)
        print(result)

        if choice.startswith("go "):
            show_location = False

        if choice == "undo" and result != "Nothing to undo.":
            show_location = True

        if choice == "restart":
            show_location = True

        # TODO: Add in code to deal with special locations (e.g. puzzles) as needed for your game
