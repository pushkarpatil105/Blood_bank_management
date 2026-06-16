"""
app.py — Flask server with all API routes for the Blood Bank Management System

Serves the frontend as static files and exposes a REST API.
On startup, loads all data from JSON files into in-memory data structures:
    - DonorQueue   (collections.deque — FIFO queue)
    - BloodInventory (Python dict — HashMap)
    - LinkedList    (manual singly linked list)
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from donor import DonorQueue
from inventory import BloodInventory
from request_list import LinkedList
from file_handler import backup_all, restore_all

# ── Flask App Setup ─────────────────────────────────────────────────

app = Flask(__name__, static_folder=None)
CORS(app)

# Path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# ── Load data structures into memory on startup ────────────────────

donor_queue = DonorQueue()
inventory = BloodInventory()
request_list = LinkedList()


# ── Serve Frontend ──────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ═══════════════════════════════════════════════════════════════════
#  API ROUTES
# ═══════════════════════════════════════════════════════════════════

# ── Donors ──────────────────────────────────────────────────────────

@app.route("/add-donor", methods=["POST"])
def add_donor():
    """Add a donor to the queue and save to JSON."""
    data = request.get_json()
    required = ["name", "age", "blood_group", "contact"]
    for field in required:
        if field not in data or not str(data[field]).strip():
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        age = int(data["age"])
        if age < 18 or age > 65:
            return jsonify({"error": "Donor age must be between 18 and 65"}), 400
    except ValueError:
        return jsonify({"error": "Age must be a number"}), 400

    donor = donor_queue.enqueue(
        name=data["name"].strip(),
        age=age,
        blood_group=data["blood_group"].strip(),
        contact=data["contact"].strip(),
        last_donation_date=data.get("last_donation_date"),
    )
    return jsonify({"message": "Donor added to queue", "donor": donor}), 201


@app.route("/process-donor", methods=["POST"])
def process_donor():
    """Dequeue the next donor, update inventory (+1 unit)."""
    donor = donor_queue.dequeue()
    if donor is None:
        return jsonify({"error": "Donor queue is empty"}), 404

    try:
        new_units = inventory.add_stock(donor["blood_group"], 1)
    except ValueError as e:
        # Re-enqueue the donor if inventory update fails
        donor_queue.enqueue(
            donor["name"], donor["age"], donor["blood_group"],
            donor["contact"], donor.get("last_donation_date")
        )
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": f"Processed donor {donor['name']}. "
                   f"{donor['blood_group']} stock now: {new_units} units.",
        "donor": donor,
        "blood_group": donor["blood_group"],
        "new_stock": new_units,
    }), 200


@app.route("/all-donors", methods=["GET"])
def all_donors():
    """Return all donors in the queue."""
    return jsonify({"donors": donor_queue.get_all()}), 200


# ── Inventory ───────────────────────────────────────────────────────

@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Return the full blood stock HashMap."""
    return jsonify({"inventory": inventory.get_full_stock()}), 200


# ── Blood Requests (Linked List) ───────────────────────────────────

@app.route("/add-request", methods=["POST"])
def add_request():
    """Add a blood request node to the linked list."""
    data = request.get_json()
    required = ["patient_name", "blood_group", "quantity", "hospital_name"]
    for field in required:
        if field not in data or not str(data[field]).strip():
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        quantity = int(data["quantity"])
        if quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
    except ValueError:
        return jsonify({"error": "Quantity must be a number"}), 400

    req = request_list.insert(
        patient_name=data["patient_name"].strip(),
        blood_group=data["blood_group"].strip(),
        quantity=quantity,
        hospital_name=data["hospital_name"].strip(),
    )
    return jsonify({"message": "Blood request added", "request": req}), 201


@app.route("/all-requests", methods=["GET"])
def all_requests():
    """Return all requests from the linked list."""
    return jsonify({"requests": request_list.traverse()}), 200


@app.route("/fulfill-request", methods=["POST"])
def fulfill_request():
    """Mark a request as fulfilled and reduce inventory."""
    data = request.get_json()
    req_id = data.get("request_id")
    if req_id is None:
        return jsonify({"error": "Missing request_id"}), 400

    req = request_list.search(int(req_id))
    if req is None:
        return jsonify({"error": "Request not found"}), 404
    if req["status"] == "fulfilled":
        return jsonify({"error": "Request already fulfilled"}), 400

    # Try to reduce stock
    try:
        inventory.reduce_stock(req["blood_group"], req["quantity"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    updated = request_list.update_status(int(req_id), "fulfilled")
    return jsonify({
        "message": f"Request #{req_id} fulfilled. "
                   f"{req['quantity']} unit(s) of {req['blood_group']} deducted.",
        "request": updated,
    }), 200


# ── Match Donor ─────────────────────────────────────────────────────

@app.route("/match-donor", methods=["GET"])
def match_donor():
    """
    Check blood group compatibility.
    Query param: blood_group (the recipient needs this type).
    Returns compatible donor blood groups with available units,
    and matching registered donors from the queue.
    """
    blood_group = request.args.get("blood_group", "").strip().upper()
    if not blood_group:
        return jsonify({"error": "Missing query param: blood_group"}), 400

    compatible_stock = inventory.get_compatible_stock(blood_group)
    compatible_donors = []
    for bg in inventory.get_compatible_donors(blood_group):
        compatible_donors.extend(donor_queue.get_donors_by_blood_group(bg))

    return jsonify({
        "requested_blood_group": blood_group,
        "compatible_stock": compatible_stock,
        "compatible_donors": compatible_donors,
        "total_compatible_units": sum(compatible_stock.values()),
    }), 200


# ── Report ──────────────────────────────────────────────────────────

@app.route("/report", methods=["GET"])
def report():
    """
    Return statistics:
    - total donors in queue
    - full stock summary
    - fulfilled vs pending request counts
    - low-stock groups (below 5 units)
    """
    all_reqs = request_list.traverse()
    pending = [r for r in all_reqs if r["status"] == "pending"]
    fulfilled = [r for r in all_reqs if r["status"] == "fulfilled"]
    stock = inventory.get_full_stock()
    low_stock = inventory.get_low_stock_groups(threshold=5)

    return jsonify({
        "total_donors_in_queue": donor_queue.size(),
        "stock_summary": stock,
        "total_stock": sum(stock.values()),
        "total_requests": len(all_reqs),
        "pending_requests": len(pending),
        "fulfilled_requests": len(fulfilled),
        "low_stock_groups": low_stock,
    }), 200


# ── Backup & Restore ───────────────────────────────────────────────

@app.route("/backup", methods=["POST"])
def backup():
    """Backup all JSON files to data/backup/."""
    try:
        backup_all()
        return jsonify({"message": "Backup created successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Backup failed: {str(e)}"}), 500


@app.route("/restore", methods=["POST"])
def restore():
    """Restore all JSON files from data/backup/ and reload in-memory data."""
    try:
        restore_all()
        # Reload in-memory data structures from restored files
        donor_queue.reload()
        inventory.reload()
        request_list.reload()
        return jsonify({"message": "Data restored from backup successfully"}), 200
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Restore failed: {str(e)}"}), 500


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  Blood Bank Management System — Flask Server")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 55)
    app.run(debug=True, port=5000)
