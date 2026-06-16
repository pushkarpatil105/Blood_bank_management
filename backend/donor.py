"""
donor.py — Donor logic + Queue implementation using collections.deque

Data Structure: Queue (FIFO) via collections.deque
    - New donors are enqueued (appended to the right).
    - When processing a donation, the next donor in line is dequeued
      (popped from the left).

Why Queue / deque?
    Donor registrations should be served in First-In-First-Out order,
    ensuring fairness.  collections.deque gives O(1) append and popleft,
    making it optimal for a FIFO queue.

Donor Fields:
    donor_id, name, age, blood_group, contact, last_donation_date
"""

from collections import deque
from datetime import datetime
from file_handler import load_donors, save_donors


class DonorQueue:
    """
    FIFO Queue of registered donors backed by collections.deque.

    All mutations are immediately persisted to donors.json.
    """

    def __init__(self):
        """Load existing donors from JSON into the Queue."""
        donors_list = load_donors()
        self.queue = deque(donors_list)        # deque ← list
        # Track the next auto-increment id
        if donors_list:
            self._next_id = max(d.get("donor_id", 0) for d in donors_list) + 1
        else:
            self._next_id = 1

    # ── Queue Operations ────────────────────────────────────────────

    def enqueue(self, name, age, blood_group, contact, last_donation_date=None):
        """
        Register a new donor — enqueue at the rear of the queue.

        Time complexity: O(1) amortized (deque.append).
        """
        donor = {
            "donor_id": self._next_id,
            "name": name,
            "age": age,
            "blood_group": blood_group.upper(),
            "contact": contact,
            "last_donation_date": last_donation_date or datetime.now().strftime("%Y-%m-%d"),
        }
        self.queue.append(donor)               # O(1)
        self._next_id += 1
        self._persist()
        return donor

    def dequeue(self):
        """
        Process the next donor in line — dequeue from the front.

        Time complexity: O(1) (deque.popleft).
        Returns the donor dict, or None if the queue is empty.
        """
        if not self.queue:
            return None
        donor = self.queue.popleft()           # O(1)
        self._persist()
        return donor

    def peek(self):
        """Return the front donor without removing (O(1))."""
        return self.queue[0] if self.queue else None

    def size(self):
        """Return the number of donors in the queue."""
        return len(self.queue)

    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.queue) == 0

    def get_all(self):
        """Return all donors in queue order (front → rear)."""
        return list(self.queue)

    def get_donors_by_blood_group(self, blood_group):
        """Filter donors by blood group."""
        blood_group = blood_group.upper()
        return [d for d in self.queue if d["blood_group"] == blood_group]

    # ── Persistence ─────────────────────────────────────────────────

    def _persist(self):
        """Save the current queue contents to donors.json."""
        save_donors(list(self.queue))

    def reload(self):
        """Re-read donors from disk (useful after restore)."""
        donors_list = load_donors()
        self.queue = deque(donors_list)
        if donors_list:
            self._next_id = max(d.get("donor_id", 0) for d in donors_list) + 1
        else:
            self._next_id = 1
