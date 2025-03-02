Overview

This project is an Attendance Management System that uses facial recognition technology to mark attendance. It consists of two main components:

Take Attendance: A live attendance system that uses a webcam to detect and recognize faces, marking attendance in real-time.

Manage Students: A student management system that allows administrators to register new students, view attendance data, and generate reports.

The system is built using Python and leverages several libraries for facial recognition, database management, and user interface.


This document provides an overview of the libraries used in the take_attendance.py script and other related scripts for the attendance system. The system is designed to automate the process of taking attendance using facial recognition and storing the data in a database. Below is a detailed explanation of each library used in the project.

1. pymysql
Purpose: pymysql is a Python library used to connect to and interact with MySQL databases.

Usage: In this project, it is used to connect to the MySQL database where attendance records are stored. It allows the script to execute SQL queries, such as inserting new attendance records or fetching existing ones.

Installation:

bash
Copy
pip install pymysql

2. streamlit
Purpose: streamlit is a powerful library for building interactive web applications with Python.

Usage: It is used to create a user-friendly interface for the attendance system. Users can interact with the system through a web browser, view attendance records, and perform other tasks.

Installation:

bash
Copy
pip install streamlit

3. face_recognition
Purpose: face_recognition is a library for facial recognition tasks. It can detect and recognize faces in images or video streams.

Usage: In this project, it is used to identify students by comparing their faces with pre-registered images. It helps in automating the attendance process.

Installation:

bash
Copy
pip install face_recognition

4. opencv-python (cv2)
Purpose: opencv-python (commonly imported as cv2) is a library for computer vision tasks, such as image and video processing.

Usage: It is used to capture video from the camera, process frames, and display the video feed in real-time during the attendance process.

Installation:

bash
Copy
pip install opencv-python

5. numpy
Purpose: numpy is a library for numerical computing in Python. It provides support for arrays, matrices, and mathematical operations.

Usage: It is used to handle image data (e.g., converting images to arrays) and perform mathematical operations required for facial recognition.

Installation:

bash
Copy
pip install numpy

6. os
Purpose: The os module is a built-in Python library for interacting with the operating system.

Usage: It is used to handle file and directory operations, such as reading images from a folder or checking if a file exists.

Installation: No installation is required as it is part of Python's standard library.


7. datetime
Purpose: The datetime module is a built-in Python library for working with dates and times.

Usage: It is used to record the date and time when attendance is taken and to format timestamps for display or storage.

Installation: No installation is required as it is part of Python's standard library.


8. playsound
Purpose: playsound is a library for playing audio files.

Usage: It is used to play a sound (e.g., a beep) when attendance is successfully recorded.

Installation:

bash
Copy
pip install playsound


9. pandas
Purpose: pandas is a library for data manipulation and analysis. It provides data structures like DataFrames for handling tabular data.

Usage: It is used to organize and process attendance data, such as exporting records to Excel or CSV files.

Installation:

bash
Copy
pip install pandas


10. python-docx
Purpose: python-docx is a library for creating and updating Microsoft Word (.docx) files.

Usage: It is used to generate attendance reports in Word format.

Installation:

bash
Copy
pip install python-docx


11. python-dateutil
Purpose: python-dateutil is a library for extending Python's datetime module with additional functionality.

Usage: It is used for advanced date and time manipulations, such as calculating time differences or parsing date strings.

Installation:

bash
Copy
pip install python-dateutil


12. cryptography
Purpose: cryptography is a library for secure communication and data encryption.

Usage: It is used to secure sensitive data, such as database credentials or attendance records.

Installation:

bash
Copy
pip install cryptography


13. openpyxl
Purpose: openpyxl is a library for reading and writing Excel files (.xlsx).

Usage: It is used to export attendance records to Excel format for easy sharing and analysis.

Installation:

bash
Copy
pip install openpyxl
Additional Notes
Upgrading setuptools: Before installing some libraries, you may need to upgrade setuptools to ensure compatibility:

bash
Copy
pip install --upgrade setuptools
Face Recognition Models: Some face recognition models are hosted on GitHub. You can install them using:

bash
Copy
pip install git+https://github.com/ageitgey/face_recognition_models


Troubleshooting
Camera Not Working:

Ensure your webcam is properly connected and accessible.

Grant camera permissions to your browser if running on a local server.

Database Connection Issues:

Verify your MySQL credentials in db_config.py.

Ensure the MySQL server is running.

Face Recognition Errors:

Ensure images in the known_faces folder are clear and contain only one face per image.

Use high-quality images for better recognition accuracy.

Sound Not Playing:

Ensure the att_marked.mp3 file is placed in the correct directory.

Check your system's audio settings.


Notes
The system is designed for educational purposes and can be customized as needed.

For large-scale deployments, consider optimizing the database and facial recognition algorithms for better performance.



SQL CODE 

USE attendance_system;



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

-- Query to view all attendance records
SELECT * FROM attendance;