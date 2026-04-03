"""
E-Library Digital Book Access System
Backend: FastAPI + MySQL
TCET | AI & Data Science Department
"""
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import mysql.connector, hashlib
from datetime import datetime, timedelta
 
app = FastAPI(title="E-Library API", version="1.0")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ── MYSQL CONNECTION CONFIG ───────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # ← your MySQL username
    "password": "Ankush82006#",  # ← your MySQL password
    "database": "elibrary"       # ← database name you created
}
 
def get_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn
 
# ── MODELS ────────────────────────────────────────────────────
 
class UserLogin(BaseModel):
    email: str
    password: str
 
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    membership_type: str = "standard"
 
class BorrowRequest(BaseModel):
    user_id: int
    book_id: int
 
class ReturnRequest(BaseModel):
    record_id: int
 
class ReviewRequest(BaseModel):
    user_id: int
    book_id: int
    rating: int
    comment: Optional[str] = None
 
class WishlistRequest(BaseModel):
    user_id: int
    book_id: int
 
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
 
# ── AUTH ROUTES ──────────────────────────────────────────────
 
@app.post("/api/register")
def register(data: UserRegister):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        max_books = 5 if data.membership_type == "premium" else 3
        cursor.execute(
            "INSERT INTO Users (name, email, password_hash, membership_type, max_books) VALUES (%s,%s,%s,%s,%s)",
            (data.name, data.email, hash_password(data.password), data.membership_type, max_books)
        )
        conn.commit()
        return {"success": True, "message": "Registered successfully!"}
    except mysql.connector.IntegrityError:
        raise HTTPException(400, "Email already registered.")
    finally:
        cursor.close(); conn.close()
 
@app.post("/api/login")
def login(data: UserLogin):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM Users WHERE email=%s AND password_hash=%s AND is_active=1",
        (data.email, hash_password(data.password))
    )
    user = cursor.fetchone()
    cursor.close(); conn.close()
    if not user:
        raise HTTPException(401, "Invalid credentials.")
    return {
        "success": True,
        "user": {
            "user_id":         user["user_id"],
            "name":            user["name"],
            "email":           user["email"],
            "membership_type": user["membership_type"],
            "max_books":       user["max_books"]
        }
    }
 
# ── BOOK ROUTES ──────────────────────────────────────────────
 
@app.get("/api/books")
def get_books(search: Optional[str] = None, category: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT b.book_id, b.title, a.name AS author, c.name AS category,
               b.available_copies, b.total_copies, b.published_year,
               b.description, b.isbn, b.publisher
        FROM Books b
        JOIN Authors a    ON b.author_id   = a.author_id
        JOIN Categories c ON b.category_id = c.category_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (b.title LIKE %s OR a.name LIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    if category:
        query += " AND c.name = %s"
        params.append(category)
    query += " ORDER BY b.title"
    cursor.execute(query, params)
    books = cursor.fetchall()
    cursor.close(); conn.close()
    return books
 
@app.get("/api/books/top-borrowed")
def top_borrowed():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vw_TopBorrowed LIMIT 5")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows
 
@app.get("/api/books/{book_id}")
def get_book(book_id: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, a.name AS author, c.name AS category,
               ROUND(AVG(r.rating),1) AS avg_rating,
               COUNT(r.review_id) AS review_count
        FROM Books b
        JOIN Authors a    ON b.author_id   = a.author_id
        JOIN Categories c ON b.category_id = c.category_id
        LEFT JOIN Reviews r ON b.book_id   = r.book_id
        WHERE b.book_id = %s
        GROUP BY b.book_id
    """, (book_id,))
    book = cursor.fetchone()
    cursor.execute("""
        SELECT u.name, r.rating, r.comment, r.reviewed_at
        FROM Reviews r JOIN Users u ON r.user_id = u.user_id
        WHERE r.book_id = %s ORDER BY r.reviewed_at DESC
    """, (book_id,))
    reviews = cursor.fetchall()
    cursor.close(); conn.close()
    if not book:
        raise HTTPException(404, "Book not found.")
    return {"book": book, "reviews": reviews}
 
@app.get("/api/categories")
def get_categories():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Categories")
    cats = cursor.fetchall()
    cursor.close(); conn.close()
    return cats
 
# ── BORROW / RETURN ──────────────────────────────────────────
 
@app.post("/api/borrow")
def borrow_book(req: BorrowRequest):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
 
    cursor.execute("SELECT available_copies, title FROM Books WHERE book_id=%s", (req.book_id,))
    book = cursor.fetchone()
    if not book:
        raise HTTPException(404, "Book not found.")
    if book["available_copies"] < 1:
        raise HTTPException(400, f"'{book['title']}' is currently not available.")
 
    cursor.execute("SELECT max_books FROM Users WHERE user_id=%s", (req.user_id,))
    user = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM BorrowRecords WHERE user_id=%s AND status='active'", (req.user_id,)
    )
    active_count = cursor.fetchone()["cnt"]
    if active_count >= user["max_books"]:
        raise HTTPException(400, f"Borrow limit reached ({user['max_books']} books max).")
 
    cursor.execute(
        "SELECT 1 FROM BorrowRecords WHERE user_id=%s AND book_id=%s AND status='active'",
        (req.user_id, req.book_id)
    )
    if cursor.fetchone():
        raise HTTPException(400, "You already have this book borrowed.")
 
    due = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO BorrowRecords (user_id, book_id, due_date) VALUES (%s,%s,%s)",
        (req.user_id, req.book_id, due)
    )
    conn.commit()
    cursor.close(); conn.close()
    return {"success": True, "message": f"'{book['title']}' borrowed! Due: {due[:10]}"}
 
@app.post("/api/return")
def return_book(req: ReturnRequest):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM BorrowRecords WHERE record_id=%s AND status='active'", (req.record_id,)
    )
    record = cursor.fetchone()
    if not record:
        raise HTTPException(404, "Active borrow record not found.")
    cursor.execute(
        "UPDATE BorrowRecords SET status='returned', returned_at=%s WHERE record_id=%s",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), req.record_id)
    )
    conn.commit()
    cursor.close(); conn.close()
    return {"success": True, "message": "Book returned successfully!"}
 
# ── USER ROUTES ──────────────────────────────────────────────
 
@app.get("/api/user/{user_id}/borrowed")
def user_borrowed(user_id: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT br.record_id, b.title, a.name AS author,
               br.borrowed_at, br.due_date, br.status
        FROM BorrowRecords br
        JOIN Books b   ON br.book_id  = b.book_id
        JOIN Authors a ON b.author_id = a.author_id
        WHERE br.user_id = %s ORDER BY br.borrowed_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows
 
@app.get("/api/user/{user_id}/wishlist")
def get_wishlist(user_id: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT w.wishlist_id, b.book_id, b.title, a.name AS author,
               b.available_copies, c.name AS category
        FROM Wishlist w
        JOIN Books b      ON w.book_id     = b.book_id
        JOIN Authors a    ON b.author_id   = a.author_id
        JOIN Categories c ON b.category_id = c.category_id
        WHERE w.user_id = %s
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows
 
@app.post("/api/wishlist")
def toggle_wishlist(req: WishlistRequest):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT 1 FROM Wishlist WHERE user_id=%s AND book_id=%s", (req.user_id, req.book_id)
    )
    exists = cursor.fetchone()
    if exists:
        cursor.execute("DELETE FROM Wishlist WHERE user_id=%s AND book_id=%s", (req.user_id, req.book_id))
        msg = "Removed from wishlist."
    else:
        cursor.execute("INSERT INTO Wishlist (user_id, book_id) VALUES (%s,%s)", (req.user_id, req.book_id))
        msg = "Added to wishlist!"
    conn.commit()
    cursor.close(); conn.close()
    return {"success": True, "message": msg}
 
# ── REVIEWS ──────────────────────────────────────────────────
 
@app.post("/api/review")
def add_review(req: ReviewRequest):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO Reviews (user_id, book_id, rating, comment) VALUES (%s,%s,%s,%s)",
            (req.user_id, req.book_id, req.rating, req.comment)
        )
        conn.commit()
        return {"success": True, "message": "Review submitted!"}
    except mysql.connector.IntegrityError:
        raise HTTPException(400, "You already reviewed this book.")
    finally:
        cursor.close(); conn.close()
 
# ── STATS ────────────────────────────────────────────────────
 
@app.get("/api/stats")
def get_stats():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS cnt FROM Books"); total_books = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) AS cnt FROM Users WHERE membership_type != 'admin'"); total_users = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) AS cnt FROM BorrowRecords WHERE status='active'"); active_borrows = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) AS cnt FROM BorrowRecords"); total_borrows = cursor.fetchone()["cnt"]
    cursor.close(); conn.close()
    return {
        "total_books":    total_books,
        "total_users":    total_users,
        "active_borrows": active_borrows,
        "total_borrows":  total_borrows
    }
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend_mysql:app", host="0.0.0.0", port=8000, reload=True)