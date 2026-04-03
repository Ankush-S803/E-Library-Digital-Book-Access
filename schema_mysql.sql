DROP DATABASE IF EXISTS elibrary;
CREATE DATABASE elibrary;
USE elibrary;

CREATE TABLE Authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author_id INT,
    category_id INT,
    available_copies INT NOT NULL DEFAULT 0,
    total_copies INT NOT NULL DEFAULT 0,
    published_year INT,
    description TEXT,
    isbn VARCHAR(20),
    publisher VARCHAR(100),
    FOREIGN KEY (author_id) REFERENCES Authors(author_id),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    membership_type VARCHAR(20) DEFAULT 'standard',
    max_books INT DEFAULT 3,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE BorrowRecords (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    book_id INT,
    status VARCHAR(20) DEFAULT 'active',
    borrowed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    returned_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (book_id) REFERENCES Books(book_id)
);

CREATE TABLE Wishlist (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    book_id INT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (book_id) REFERENCES Books(book_id),
    UNIQUE (user_id, book_id)
);

CREATE TABLE Reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    book_id INT,
    rating INT,
    comment TEXT,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (book_id) REFERENCES Books(book_id),
    UNIQUE (user_id, book_id)
);

-- Triggers for handling available_copies
DELIMITER //

CREATE TRIGGER after_borrow_insert
AFTER INSERT ON BorrowRecords
FOR EACH ROW
BEGIN
    IF NEW.status = 'active' THEN
        UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = NEW.book_id;
    END IF;
END;
//

CREATE TRIGGER after_borrow_update
AFTER UPDATE ON BorrowRecords
FOR EACH ROW
BEGIN
    IF OLD.status = 'active' AND NEW.status = 'returned' THEN
        UPDATE Books SET available_copies = available_copies + 1 WHERE book_id = NEW.book_id;
    END IF;
END;
//

DELIMITER ;

-- View for top borrowed books
CREATE VIEW vw_TopBorrowed AS
SELECT b.book_id, b.title, a.name AS author, c.name AS category,
       b.available_copies, b.total_copies, COUNT(br.record_id) AS borrow_count
FROM Books b
JOIN Authors a ON b.author_id = a.author_id
JOIN Categories c ON b.category_id = c.category_id
LEFT JOIN BorrowRecords br ON b.book_id = br.book_id
GROUP BY b.book_id
ORDER BY borrow_count DESC;

-- Seed Data
INSERT INTO Authors (name) VALUES 
('J.K. Rowling'), ('George R.R. Martin'), ('J.R.R. Tolkien'), ('F. Scott Fitzgerald'), ('Jane Austen');

INSERT INTO Categories (name) VALUES 
('Fantasy'), ('Fiction'), ('Romance'), ('Sci-Fi'), ('Mystery');

INSERT INTO Books (title, author_id, category_id, available_copies, total_copies, published_year, description, isbn, publisher) VALUES
('Harry Potter and the Sorcerer''s Stone', 1, 1, 5, 5, 1997, 'A boy wizard begins his journey.', '9780590353403', 'Scholastic'),
('A Game of Thrones', 2, 1, 3, 3, 1996, 'First book of A Song of Ice and Fire.', '9780553103540', 'Bantam Spectra'),
('The Hobbit', 3, 1, 4, 4, 1937, 'A hobbit goes on an adventure.', '9780345339683', 'Allen & Unwin'),
('The Great Gatsby', 4, 2, 2, 2, 1925, 'A story of the Jazz Age.', '9780743273565', 'Scribner'),
('Pride and Prejudice', 5, 3, 6, 6, 1813, 'A classic romance novel.', '9781503290563', 'T. Egerton'),
('Harry Potter and the Chamber of Secrets', 1, 1, 4, 4, 1998, 'The second year at Hogwarts.', '9780439064873', 'Scholastic'),
('The Lord of the Rings', 3, 1, 5, 5, 1954, 'The epic high-fantasy novel.', '9780618640157', 'Allen & Unwin');

-- Insert admin user (admin@elibrary.com / admin123)
INSERT INTO Users (name, email, password_hash, membership_type, max_books, is_active) VALUES
('Admin', 'admin@elibrary.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', 10, TRUE);
