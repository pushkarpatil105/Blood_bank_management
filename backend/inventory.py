"""
inventory.py — HashMap implementation using Python dict

Data Structure: HashMap (Python dict)
    Key   = blood group string  (e.g. "A+", "O-")
    Value = available units     (integer ≥ 0)

Why HashMap?
    O(1) average-case lookup, insertion, and deletion — ideal for
    checking or updating stock of a specific blood group instantly.

Blood Group Compatibility Table:
    Donor Group → Can donate to these recipient groups
"""

from file_handler import load_inventory, save_inventory

# ── Compatibility map ───────────────────────────────────────────────
# Donor blood group → set of recipient blood groups it can donate to
COMPATIBILITY = {
    "O-":  {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
    "O+":  {"O+", "A+", "B+", "AB+"},
    "A-":  {"A-", "A+", "AB-", "AB+"},
    "A+":  {"A+", "AB+"},
    "B-":  {"B-", "B+", "AB-", "AB+"},
    "B+":  {"B+", "AB+"},
    "AB-": {"AB-", "AB+"},
    "AB+": {"AB+"},
}

# Reverse: recipient blood group → set of donor groups that can donate to it
RECEIVE_FROM = {}
for donor_bg, recipients in COMPATIBILITY.items():
    for recipient_bg in recipients:
        RECEIVE_FROM.setdefault(recipient_bg, set()).add(donor_bg)


class BloodInventory:
    """
    HashMap-based blood stock manager.

    Internally stores {blood_group: units} in a Python dict.
    Every mutation is immediately persisted via file_handler.
    """

    def __init__(self):
        """Load existing inventory from JSON into the HashMap."""
        self.stock = load_inventory()          # dict  →  HashMap

    # ── Core HashMap Operations ─────────────────────────────────────

    def add_stock(self, blood_group, units=1):
        """
        Increase stock for *blood_group* by *units*.

        HashMap operation: O(1) key lookup + update.
        """
        blood_group = blood_group.upper()
        if blood_group not in self.stock:
            raise ValueError(f"Invalid blood group: {blood_group}")
        self.stock[blood_group] += units       # O(1)
        save_inventory(self.stock)
        return self.stock[blood_group]

    def reduce_stock(self, blood_group, units=1):
        """
        Decrease stock for *blood_group* by *units*.
        Raises ValueError if insufficient stock.

        HashMap operation: O(1) key lookup + update.
        """
        blood_group = blood_group.upper()
        if blood_group not in self.stock:
            raise ValueError(f"Invalid blood group: {blood_group}")
        if self.stock[blood_group] < units:
            raise ValueError(
                f"Insufficient stock for {blood_group}: "
                f"available={self.stock[blood_group]}, requested={units}"
            )
        self.stock[blood_group] -= units       # O(1)
        save_inventory(self.stock)
        return self.stock[blood_group]

    def check_availability(self, blood_group):
        """
        Return available units for *blood_group*.

        HashMap operation: O(1) key lookup.
        """
        blood_group = blood_group.upper()
        return self.stock.get(blood_group, 0)  # O(1)

    def get_full_stock(self):
        """Return the entire HashMap (all blood groups + units)."""
        return dict(self.stock)

    def get_low_stock_groups(self, threshold=5):
        """Return groups with stock below *threshold*."""
        return {bg: units for bg, units in self.stock.items()
                if units < threshold}

    # ── Compatibility Helpers ───────────────────────────────────────

    @staticmethod
    def get_compatible_donors(recipient_blood_group):
        """
        Given a *recipient* blood group, return the set of donor
        blood groups that can donate to this recipient.
        """
        recipient_blood_group = recipient_blood_group.upper()
        return RECEIVE_FROM.get(recipient_blood_group, set())

    def get_compatible_stock(self, recipient_blood_group):
        """
        Return {donor_group: available_units} for all compatible
        donor groups that have stock > 0.
        """
        compatible = self.get_compatible_donors(recipient_blood_group)
        return {bg: self.stock.get(bg, 0) for bg in compatible
                if self.stock.get(bg, 0) > 0}

    def reload(self):
        """Re-read inventory from disk (useful after restore)."""
        self.stock = load_inventory()
