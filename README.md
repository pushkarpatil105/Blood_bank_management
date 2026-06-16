# 🩸 Blood Bank Management System

> **ADA Mini Project** — Analysis and Design of Algorithms  
> A full-stack blood bank management system demonstrating core data structures.

---

## 📋 Table of Contents

- [How to Run](#-how-to-run)
- [Project Structure](#-project-structure)
- [Data Structures Used](#-data-structures-used)
- [API Routes](#-api-routes)
- [Features](#-features)
- [Blood Group Compatibility](#-blood-group-compatibility)

---

## 🚀 How to Run

### Prerequisites
- Python 3.7+

### Steps

1. **Install dependencies:**
   ```bash
   pip install flask flask-cors
   ```

2. **Start the server:**
   ```bash
   python backend/app.py
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

That's it! The Flask server serves both the API and the frontend.

---

## 📁 Project Structure

```
Blood_bank_management/
├── backend/
│   ├── app.py                  # Flask server, all API routes
│   ├── donor.py                # Donor logic + Queue (collections.deque)
│   ├── inventory.py            # HashMap (Python dict) for blood stock
│   ├── request_list.py         # Manually written Singly Linked List
│   ├── file_handler.py         # Read/write JSON files + Backup/Restore
│   └── data/
│       ├── donors.json         # Persisted donor records
│       ├── inventory.json      # Blood stock per group
│       ├── requests.json       # Blood request records
│       └── backup/             # Backup copies of JSON files
├── frontend/
│   ├── index.html              # Single-page dashboard UI
│   ├── style.css               # Medical-themed stylesheet
│   └── script.js               # Fetch-based API calls & DOM updates
└── README.md
```

---

## 🧠 Data Structures Used

### 1. HashMap — `inventory.py`

| Aspect        | Detail |
|---------------|--------|
| **Implementation** | Python `dict` |
| **Key**       | Blood group string (`A+`, `O-`, etc.) |
| **Value**     | Available units (integer) |
| **Operations**| `add_stock()` O(1), `reduce_stock()` O(1), `check_availability()` O(1) |
| **Why?**      | Hash maps provide constant-time lookup, insertion, and deletion — ideal for quickly checking or updating stock of any blood group. |

### 2. Queue — `donor.py`

| Aspect        | Detail |
|---------------|--------|
| **Implementation** | `collections.deque` |
| **Order**     | FIFO (First-In, First-Out) |
| **Operations**| `enqueue()` O(1), `dequeue()` O(1), `peek()` O(1) |
| **Why?**      | Donors should be served in the order they registered — a queue guarantees fairness. `deque` provides O(1) operations for both ends. |

### 3. Singly Linked List — `request_list.py`

| Aspect        | Detail |
|---------------|--------|
| **Implementation** | Manual `Node` + `LinkedList` classes |
| **Node**      | `data` (request dict) + `next` pointer |
| **Operations**| `insert()` O(1) with tail pointer, `delete()` O(n), `traverse()` O(n), `search()` O(n) |
| **Why?**      | Demonstrates dynamic, pointer-based data structures. Efficient for sequential processing and arbitrary insertions/deletions without resizing. |

### 4. File Handling — `file_handler.py`

| Aspect        | Detail |
|---------------|--------|
| **Format**    | JSON files for human-readable persistence |
| **Operations**| `load_*()` / `save_*()` for each data type |
| **Backup**    | `backup_all()` copies JSON files to `data/backup/` |
| **Restore**   | `restore_all()` restores from `data/backup/` |

---

## 🔌 API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/add-donor` | Add donor to queue + save to JSON |
| `POST` | `/process-donor` | Dequeue donor, update inventory (+1 unit) |
| `GET`  | `/all-donors` | Return all donors in the queue |
| `POST` | `/add-request` | Add request node to linked list |
| `GET`  | `/all-requests` | Return all requests from linked list |
| `POST` | `/fulfill-request` | Mark request as fulfilled, reduce stock |
| `GET`  | `/match-donor` | Check compatibility, return matching donors + stock |
| `GET`  | `/inventory` | Return full blood stock HashMap |
| `GET`  | `/report` | Stats: donors, stock, requests, low-stock alerts |
| `POST` | `/backup` | Backup all JSON files |
| `POST` | `/restore` | Restore from backup |

---

## ✨ Features

- **Dashboard** — Real-time blood availability overview with low-stock alerts
- **Donor Registration** — Add donors to a FIFO queue
- **Donor Processing** — Dequeue next donor and automatically update inventory
- **Blood Requests** — Submit and track blood requests (pending/fulfilled)
- **Donor Matching** — Find compatible donors and available stock based on blood group compatibility rules
- **Reports** — Full statistics: total donors, stock summary, request breakdown, low-stock groups
- **Backup & Restore** — One-click data backup and restore

---

## 🔴 Blood Group Compatibility

| Donor | Can Donate To |
|-------|---------------|
| O-    | Everyone (Universal Donor) |
| O+    | O+, A+, B+, AB+ |
| A-    | A-, A+, AB-, AB+ |
| A+    | A+, AB+ |
| B-    | B-, B+, AB-, AB+ |
| B+    | B+, AB+ |
| AB-   | AB-, AB+ |
| AB+   | AB+ only |

---

## 🛠️ Tech Stack

- **Frontend:** HTML + CSS + Vanilla JavaScript (single page, no framework)
- **Backend:** Python + Flask
- **Storage:** JSON files (local, no database)

---

*Built as an ADA (Analysis and Design of Algorithms) mini project.*
