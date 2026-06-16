"""
request_list.py — Manually written Singly Linked List for blood requests

Data Structure: Singly Linked List
    - Node class: holds data (dict) + next pointer.
    - LinkedList class: insert at end, delete by request_id,
      traverse (return all), search by request_id.

Why Linked List?
    Demonstrates dynamic memory allocation and pointer-based data
    structures.  Insertions at the tail are O(1) when a tail pointer
    is maintained, and deletions of arbitrary nodes are O(n) — a
    useful contrast to the O(1) HashMap and Queue operations used
    elsewhere in the project.

Request Fields:
    request_id, patient_name, blood_group, quantity,
    hospital_name, status (pending / fulfilled)
"""

from file_handler import load_requests, save_requests


class Node:
    """A single node in the singly linked list."""

    __slots__ = ("data", "next")

    def __init__(self, data):
        self.data = data       # dict with request fields
        self.next = None       # pointer to next Node


class LinkedList:
    """
    Singly Linked List of blood requests with tail pointer.

    All mutations are immediately persisted to requests.json.
    """

    def __init__(self):
        """Load existing requests from JSON and build the linked list."""
        self.head = None
        self.tail = None
        self._size = 0
        self._next_id = 1

        # Reconstruct list from persisted data
        requests_list = load_requests()
        for req in requests_list:
            self._append_node(req)

        if requests_list:
            self._next_id = max(r.get("request_id", 0) for r in requests_list) + 1

    # ── Internal helpers ────────────────────────────────────────────

    def _append_node(self, data):
        """
        Low-level append — does NOT persist (used during init).
        Time complexity: O(1) with tail pointer.
        """
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def _persist(self):
        """Save the full linked list to requests.json."""
        save_requests(self.traverse())

    # ── Public Linked List Operations ───────────────────────────────

    def insert(self, patient_name, blood_group, quantity, hospital_name, status="pending"):
        """
        Insert a new blood request at the end of the list.

        Time complexity: O(1) — tail pointer maintained.
        """
        request = {
            "request_id": self._next_id,
            "patient_name": patient_name,
            "blood_group": blood_group.upper(),
            "quantity": quantity,
            "hospital_name": hospital_name,
            "status": status,
        }
        self._append_node(request)
        self._next_id += 1
        self._persist()
        return request

    def delete(self, request_id):
        """
        Delete the node whose request_id matches.

        Time complexity: O(n) — linear scan to find the node.
        Returns the deleted request dict, or None if not found.
        """
        prev = None
        current = self.head
        while current is not None:
            if current.data.get("request_id") == request_id:
                # Unlink the node
                if prev is None:
                    self.head = current.next
                else:
                    prev.next = current.next
                # Update tail if we removed the last node
                if current == self.tail:
                    self.tail = prev
                self._size -= 1
                self._persist()
                return current.data
            prev = current
            current = current.next
        return None

    def traverse(self):
        """
        Return all requests as a list of dicts (head → tail order).

        Time complexity: O(n).
        """
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result

    def search(self, request_id):
        """
        Search for a request by request_id.

        Time complexity: O(n) — linear scan.
        Returns the request dict or None.
        """
        current = self.head
        while current is not None:
            if current.data.get("request_id") == request_id:
                return current.data
            current = current.next
        return None

    def update_status(self, request_id, new_status):
        """
        Update the status field of a request node.

        Time complexity: O(n) — linear scan.
        """
        current = self.head
        while current is not None:
            if current.data.get("request_id") == request_id:
                current.data["status"] = new_status
                self._persist()
                return current.data
            current = current.next
        return None

    def size(self):
        """Return the number of requests in the list."""
        return self._size

    def reload(self):
        """Re-read requests from disk (useful after restore)."""
        self.head = None
        self.tail = None
        self._size = 0
        requests_list = load_requests()
        for req in requests_list:
            self._append_node(req)
        if requests_list:
            self._next_id = max(r.get("request_id", 0) for r in requests_list) + 1
        else:
            self._next_id = 1
