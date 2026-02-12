"""CSC111 Assignment 1: Text Adventure Game - Event Logger

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Assignment 1. Please consult
the project handout for instructions and details.

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
from dataclasses import dataclass
from typing import Optional


# Note: We have completed the Event class for you. Do NOT modify it here for A1.
@dataclass
class Event:
    """
    A node representing one event in an adventure game.

    Instance Attributes:
    - id_num: Integer id of this event's location
    - description: Long description of this event's location
    - next_command: String command which leads this event to the next event, None if this is the last game event
    - next: Event object representing the next event in the game, or None if this is the last game event
    - prev: Event object representing the previous event in the game, None if this is the first game event
    """
    id_num: int
    description: str
    next_command: Optional[str] = None
    next: Optional[Event] = None
    prev: Optional[Event] = None


class EventList:
    """
    A linked list of game events.

    Instance Attributes:
        - first: The first event in this list, or None if the list is empty.
        - last: The last event in this list, or None if the list is empty.

    Representation Invariants:
        - (self.first is None) == (self.last is None)
        - If self.first is not None, then self.first.prev is None
        - If self.last is not None, then self.last.next is None
    """
    first: Optional[Event]
    last: Optional[Event]

    def __init__(self) -> None:
        """Initialize a new empty event list."""
        self.first = None
        self.last = None

    def display_events(self) -> None:
        """Display all events in chronological order."""
        curr = self.first
        while curr is not None:
            # Show the command that led FROM this event to the next.
            # If curr is the last event, next_command will be None.
            cmd = curr.next_command if curr.next_command is not None else "(end)"
            print(f"Location: {curr.id_num}, Command: {cmd}")
            curr = curr.next

    def get_events_as_string(self) -> str:
        """Return a string showing all events in chronological order.
        This is useful for Project 1 (so the game manager can print it).
        """
        lines = []
        curr = self.first
        while curr is not None:
            cmd = curr.next_command if curr.next_command is not None else "(end)"
            lines.append(f"Location: {curr.id_num}, Command: {cmd}")
            curr = curr.next
        return "\n".join(lines) if lines else "(no events)"

    def is_empty(self) -> bool:
        """Return whether this event list is empty."""
        return self.first is None

    def add_event(self, event: Event, command: str = None) -> None:
        """
        Add the given new event to the end of this event list.
        The given command is the command which was used to reach this new event, or None if this is the first
        event in the game.

        IMPORTANT LINKED-LIST IDEA:
        - The <command> is stored on the *previous* node as its next_command,
          because next_command means "how to get from this node to the next node".
        """
        event.next = None
        event.next_command = None

        if self.is_empty():
            event.prev = None
            self.first = event
            self.last = event
        else:
            # Update the old last node to point to this new event
            assert self.last is not None
            self.last.next_command = command
            event.prev = self.last
            self.last.next = event
            self.last = event

    def remove_last_event(self) -> None:
        """
        Remove the last event from this event list.
        If the list is empty, do nothing.
        """
        if self.is_empty():
            return

        assert self.last is not None
        if self.first is self.last:
            self.first = None
            self.last = None
        else:
            new_last = self.last.prev
            assert new_last is not None
            new_last.next = None
            new_last.next_command = None

            self.last.prev = None
            self.last = new_last

    def get_id_log(self) -> list[int]:
        """Return a list of all location IDs visited for each event in this list, in sequence."""
        id_lst = []
        curr = self.first
        while curr is not None:
            id_lst.append(curr.id_num)
            curr = curr.next
        return id_lst

    def to_list(self) -> list[tuple[int, str, str]]:
        """Return events as a list of (location_id, description, command_to_next).

        Note: For the last event, command_to_next will be '' (empty string) because there is no next event.
        """
        out = []
        curr = self.first
        while curr is not None:
            cmd = curr.next_command if curr.next_command is not None else ""
            out.append((curr.id_num, curr.description, cmd))
            curr = curr.next
        return out

    def load_from_list(self, data: list[tuple[int, str, str]]) -> None:
        """Replace current events with the events in data.

        data is a list of (loc_id, description, command_to_next).
        We rebuild the Event nodes and restore next_command values.
        """
        self.first = None
        self.last = None

        if not data:
            return

        # Create all event nodes first
        nodes: list[Event] = [Event(loc_id, desc) for (loc_id, desc, _cmd) in data]

        # Link them + restore next_command on each node (except last)
        for i in range(len(nodes) - 1):
            nodes[i].next = nodes[i + 1]
            nodes[i + 1].prev = nodes[i]
            nodes[i].next_command = data[i][2] if data[i][2] != "" else None

        # Last node fields
        nodes[-1].next = None
        nodes[-1].next_command = None
        nodes[0].prev = None

        self.first = nodes[0]
        self.last = nodes[-1]


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'allowed-io': ['EventList.display_events'],
        'disable': ['R1705', 'static_type_checker']
    })