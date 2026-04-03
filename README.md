# E-Library-Digital-Book-Access
A full-stack digital library management system built with **FastAPI + MySQL + HTML/CSS/JS** as part of the In-House Internship at **TCET, Department of AI & Data Science**.

---

## 🚀 Features

- 🔐 User Authentication (Register / Login with SHA-256 hashing)
- 📖 Browse & Search books by title, author, or category
- 📥 Borrow books with auto availability update (via MySQL Triggers)
- ↩️ Return books with auto copy restoration
- ❤️ Wishlist management
- ⭐ Book reviews with star ratings
- 📊 Live dashboard stats (total books, members, active borrows)
- 🏷️ Membership tiers: Standard (3 books) / Premium (5 books) / Admin

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Database | MySQL, MySQL Workbench |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Auth | SHA-256 Password Hashing |
| ORM | mysql-connector-python |

---

## 🗄️ Database Schema

7 Tables with full relational structure:

- `Authors` — Book author details
- `Categories` — Book categories
- `Books` — Book inventory with copy tracking
- `Users` — Member accounts with membership type
- `BorrowRecords` — Borrow/return history
- `Wishlist` — User saved books
- `Reviews` — Star ratings and comments

**Views:** `vw_TopBorrowed`, `vw_AvailableBooks`, `vw_OverdueBooks`

**Triggers:**
- `after_borrow_insert` → auto decrements `available_copies`
- `after_borrow_update` → auto increments `available_copies` on return

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Ankush-S803/E-Library-Digital-Book-Access.git
cd E-Library-Digital-Book-Access
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn mysql-connector-python
```

### 3. Setup MySQL Database
Open MySQL Workbench and run:
```sql
CREATE DATABASE elibrary;
USE elibrary;
```
Then execute the full `schema_mysql.sql` file.

### 4. Configure Database Connection
Open `backend_mysql.py` and update:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "YOUR_PASSWORD",
    "database": "elibrary"
}
```

### 5. Run the backend
```bash
python backend_mysql.py
```

### 6. Open the frontend
Double-click `frontend.html` in File Explorer.

---

## 🔑 Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@elibrary.com | admin123 | Admin |

---

## 📁 Project Structure
E-Library-Digital-Book-Access/
├── backend_mysql.py     ← FastAPI backend
├── schema_mysql.sql     ← MySQL schema + seed data
└── frontend.html        ← UI (HTML/CSS/JS)
