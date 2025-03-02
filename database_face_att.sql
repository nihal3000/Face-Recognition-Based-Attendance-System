USE attendance_system;

-- Step 1: Drop the trigger if it exists
DROP TRIGGER IF EXISTS update_status_on_entry;

-- Step 2: Drop the event if it exists
DROP EVENT IF EXISTS daily_attendance_init;

-- Step 3: Drop the stored procedure if it exists
DROP PROCEDURE IF EXISTS initialize_daily_attendance;

-- Step 4: Drop the table if it exists
DROP TABLE IF EXISTS attendance;

-- Step 5: Create a fresh attendance table
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    entry1_in VARCHAR(20),
    entry1_out VARCHAR(20),
    entry1_hours VARCHAR(20),
    entry2_in VARCHAR(20),
    entry2_out VARCHAR(20),
    entry2_hours VARCHAR(20),
    entry3_in VARCHAR(20),
    entry3_out VARCHAR(20),
    entry3_hours VARCHAR(20),
    entry4_in VARCHAR(20),
    entry4_out VARCHAR(20),
    entry4_hours VARCHAR(20),
    entry5_in VARCHAR(20),
    entry5_out VARCHAR(20),
    entry5_hours VARCHAR(20),
    total_hours VARCHAR(20),
    status VARCHAR(20) DEFAULT 'Absent',
    UNIQUE KEY unique_date_person (name, date)
);

-- Step 6: Insert default records for known students with Absent status
INSERT INTO attendance (name, date, status) VALUES
('Faraz', CURDATE(), 'Absent'),
('Naser uddin', CURDATE(), 'Absent'),
('Omer bhai TZ', CURDATE(), 'Absent'),
('Ab Rahman bhai', CURDATE(), 'Absent'),
('Ashfaq Bhai TZ', CURDATE(), 'Absent');

-- Step 7: Create the stored procedure to initialize daily records
DELIMITER //

CREATE PROCEDURE initialize_daily_attendance()
BEGIN
    -- Insert records only for people who don't already have an entry for today
    INSERT INTO attendance (name, date, status)
    SELECT DISTINCT name, CURDATE(), 'Absent'
    FROM attendance
    WHERE date < CURDATE()
    AND name NOT IN (
        SELECT name FROM attendance WHERE date = CURDATE()
    );
END //

DELIMITER ;

-- Step 8: Create the event to run the stored procedure daily
CREATE EVENT IF NOT EXISTS daily_attendance_init
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
    CALL initialize_daily_attendance();

-- Step 9: Create the trigger to update status when an entry is added
DELIMITER //

CREATE TRIGGER update_status_on_entry
BEFORE UPDATE ON attendance
FOR EACH ROW
BEGIN
    IF NEW.entry1_in IS NOT NULL OR 
       NEW.entry2_in IS NOT NULL OR 
       NEW.entry3_in IS NOT NULL OR 
       NEW.entry4_in IS NOT NULL OR 
       NEW.entry5_in IS NOT NULL THEN
        SET NEW.status = 'Present';
    END IF;
END //

DELIMITER ;

-- Step 10: Verify the table and data
SELECT * FROM attendance;

DELETE FROM attendance
WHERE name = 'Faraz' AND date = '2025-01-08';

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);