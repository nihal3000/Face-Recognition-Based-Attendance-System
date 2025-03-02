# take_attendance.py
import pymysql
import streamlit as st
import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime
from playsound import playsound
from db_config2 import get_db_connection, insert_default_attendance


# Constants
KNOWN_FACES_DIR = "known_faces"
SUCCESS_SOUND = "att_marked.mp3"  # Ensure this file exists in your project directory
CAMERA_DURATION = 20
FACE_RECOGNITION_TOLERANCE = 0.4
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Create required directories
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# Time Conversion Functions
def convert_12_to_24(time_str):
    """Convert 12-hour format to 24-hour format"""
    try:
        time_obj = datetime.strptime(time_str, '%I:%M %p')
        return time_obj.strftime('%H:%M:%S')
    except ValueError as e:
        st.error(f"Time conversion error: {e}")
        return None

def convert_24_to_12(time_str):
    """Convert 24-hour format to 12-hour format"""
    if not time_str:
        return ""
    try:
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.strftime('%I:%M %p')
    except ValueError:
        return time_str

def load_known_faces():
    """Load known faces from directory"""
    known_faces = []
    known_names = []
    
    if not os.path.exists(KNOWN_FACES_DIR):
        st.error(f"Directory {KNOWN_FACES_DIR} not found!")
        return known_faces, known_names
        
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
            try:
                filepath = os.path.join(KNOWN_FACES_DIR, filename)
                image = face_recognition.load_image_file(filepath)
                face_locations = face_recognition.face_locations(image)
                
                if not face_locations:
                    st.warning(f"No face detected in {filename}")
                    continue
                    
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_faces.append(encoding)
                known_names.append(os.path.splitext(filename)[0])
            except Exception as e:
                st.error(f"Error loading face {filename}: {e}")
    
    return known_faces, known_names



# Define a dictionary to track recognized faces across frames
recognized_faces = {}  # {name: count}
THRESHOLD_FRAMES = 5  # Number of consecutive frames needed to confirm a match

# Define a dictionary to track recognized faces across frames
recognized_faces = {}  # {name: count}
THRESHOLD_FRAMES = 5  # Number of consecutive frames needed to confirm a match
most_recognized_face = None  # Store the most detected face
recognition_count = {}  # {name: count}


def process_frame(frame, known_faces, known_names):
    """Process video frame for face recognition and mark attendance correctly."""
    try:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        attendance_marked = False
        recognized_names = []  # Store names detected in this frame

        if not face_encodings:
            print("❌ No faces detected.")
            recognition_count.clear()  # Reset if no faces are seen
            return frame, False, []  

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            face_distances = face_recognition.face_distance(known_faces, face_encoding)
            best_match_index = np.argmin(face_distances)

            # ✅ Only consider match if confidence is high
            if face_distances[best_match_index] < FACE_RECOGNITION_TOLERANCE:
                name = known_names[best_match_index]
                confidence = 1 - face_distances[best_match_index]  # Convert distance to confidence
                print(f"🔍 Detected: {name} (Confidence: {confidence:.2f})")

                # ✅ Track how many times this face is recognized
                recognition_count[name] = recognition_count.get(name, 0) + 1
                recognized_names.append(name)

            else:
                name = "Visitor"
                print("❌ Face not recognized.")

            # Reset count if multiple people appear
            if len(set(recognized_names)) > 1:
                recognition_count.clear()
                for name in recognized_names:
                    recognition_count[name] = 1

            # Scale back coordinates for display
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            # Draw rectangle and label on detected faces
            color = (0, 0, 255) if name == "Visitor" else (0, 255, 0)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left + 6, bottom + 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        print(f"📝 Recognition Count: {recognition_count}")

        return frame, attendance_marked, recognized_names  
    
    except Exception as e:
        print(f"❌ Error processing frame: {e}")
        return frame, False, []




def mark_attendance(name):
    """Mark attendance in database"""
    try:
        current_time = datetime.now()
        time_str = current_time.strftime("%I:%M %p")
        return save_attendance_to_db(name, time_str)
    except Exception as e:
        st.error(f"Error marking attendance: {e}")
        return False




MIN_REQUIRED_FRAMES = 3
def save_attendance_to_db(name, time_str):
    """Save attendance record to database with working hours calculation"""
    connection = get_db_connection()
    if connection is None:
        return False
        
    try:
        with connection.cursor() as cursor:
            today = datetime.now().strftime("%Y-%m-%d")
            time_24 = convert_12_to_24(time_str)
            if not time_24:
                return False
            
            # Ensure student is registered
            cursor.execute("SELECT name FROM userDetails WHERE name = %s", (name,))
            if not cursor.fetchone():
                st.error(f"Unregistered student detected: {name}")
                return False
            
            # Fetch all records for the current day and person
            cursor.execute("""
                SELECT * FROM attendance 
                WHERE name = %s AND date = %s
                ORDER BY entry1_in ASC
            """, (name, today))
            records = cursor.fetchall()
            
            if not records:
                # No records exist for today, insert the first entry
                cursor.execute("""
                    INSERT INTO attendance (name, date, entry1_in, status) 
                    VALUES (%s, %s, %s, 'Present')
                """, (name, today, time_24))
                # Play success sound
                if os.path.exists(SUCCESS_SOUND):
                    playsound(SUCCESS_SOUND)
                return True
            
            # Get the last record
            last_record = records[-1]
            
            # Find the next available entry (entry1_in, entry1_out, entry2_in, etc.)
            for i in range(1, 6):  # Assuming there are 5 entries (entry1 to entry5)
                entry_in = f"entry{i}_in"
                entry_out = f"entry{i}_out"
                entry_hours = f"entry{i}_hours"
                
                if not last_record[entry_in]:
                    # If entry_in is empty, this is a new in_time entry
                    if i > 1:
                        # Check the gap between the previous out_time and the current in_time
                        prev_entry_out = f"entry{i-1}_out"
                        if last_record[prev_entry_out]:
                            prev_out_time = datetime.strptime(last_record[prev_entry_out], "%H:%M:%S")
                            current_time_obj = datetime.strptime(time_24, "%H:%M:%S")
                            break_duration = (current_time_obj - prev_out_time).total_seconds() / 60
                            
                            if break_duration < 10:
                                st.info("Need at least 10 minutes break between sessions")
                                return False
                    
                    # Insert the new in_time
                    cursor.execute(f"""
                        UPDATE attendance 
                        SET {entry_in} = %s, status = 'Present'
                        WHERE name = %s AND date = %s
                    """, (time_24, name, today))
                    # Play success sound
                    if os.path.exists(SUCCESS_SOUND):
                        playsound(SUCCESS_SOUND)
                    return True
                
                elif not last_record[entry_out]:
                    # If entry_out is empty, this is an out_time entry
                    stored_time = datetime.strptime(last_record[entry_in], "%H:%M:%S")
                    current_time_obj = datetime.strptime(time_24, "%H:%M:%S")
                    time_diff_minutes = (current_time_obj - stored_time).total_seconds() / 60
                    
                    if time_diff_minutes >= 10:
                        # Update out_time and calculate working hours for this entry
                        cursor.execute(f"""
                            UPDATE attendance 
                            SET {entry_out} = %s,
                                {entry_hours} = TIMEDIFF(%s, {entry_in})
                            WHERE name = %s AND date = %s AND {entry_out} IS NULL
                        """, (time_24, time_24, name, today))
                        
                        # Calculate total_hours by summing up all entry_hours
                        cursor.execute(f"""
                            UPDATE attendance 
                            SET total_hours = ADDTIME(
                                IFNULL(entry1_hours, '00:00:00'),
                                ADDTIME(
                                    IFNULL(entry2_hours, '00:00:00'),
                                    ADDTIME(
                                        IFNULL(entry3_hours, '00:00:00'),
                                        ADDTIME(
                                            IFNULL(entry4_hours, '00:00:00'),
                                            IFNULL(entry5_hours, '00:00:00')
                                        )
                                    )
                                )
                            )
                            WHERE name = %s AND date = %s
                        """, (name, today))
                        
                        # Play success sound
                        if os.path.exists(SUCCESS_SOUND):
                            playsound(SUCCESS_SOUND)
                        return True
                    else:
                        st.info(f"Skipping update - less than 10 minutes since last entry")
                        return False
            
            # If all entries are filled, do not allow further updates
            st.info("Maximum entries reached for today")
            return False
            
    except pymysql.Error as e:
        st.error(f"Failed to save attendance: {e}")
        return False
    finally:
        connection.close()

# def take_attendance():
#     """Live attendance page"""
#     st.header("🎥 Live Attendance System")
    
#     if st.button("Take Attendance"):
#         known_faces, known_names = load_known_faces()
#         if not known_faces:
#             st.warning("No registered faces found. Please register students first.")
#             return
            
#         progress_bar = st.progress(0)
#         status_text = st.empty()
#         frame_placeholder = st.empty()
        
#         cap = cv2.VideoCapture(0)
#         if not cap.isOpened():
#             st.error("Failed to access camera. Please check camera connection.")
#             return
            
#         try:
#             start_time = datetime.now()
#             marked_names = []  # List to store names of students whose attendance is marked
            
#             while (datetime.now() - start_time).seconds < CAMERA_DURATION:
#                 progress = int(((datetime.now() - start_time).seconds / CAMERA_DURATION) * 100)
#                 progress_bar.progress(progress)
#                 status_text.text("Processing...")
                
#                 ret, frame = cap.read()
#                 if not ret:
#                     st.error("Failed to capture frame from camera")
#                     break
                    
#                 processed_frame, marked, names = process_frame(frame, known_faces, known_names)
#                 if marked:
#                     marked_names.extend(names)  # Add marked names to the list
#                 frame_placeholder.image(processed_frame, channels="BGR")
            
#             if marked_names:
#                 # Display success message with the names of students whose attendance was marked
#                 status_text.success(f"Attendance marked successfully for: {', '.join(marked_names)}")
#                 playsound(SUCCESS_SOUND)

                
#             else:
#                 status_text.warning("No faces recognized")
                
#         except Exception as e:
#             st.error(f"An error occurred: {e}")
#         finally:
#             cap.release()
#             cv2.destroyAllWindows()
#             progress_bar.empty()
#             frame_placeholder.empty()

# To keep track of the last recognized name
def take_attendance():
    """Live attendance page"""
    st.header("🎥 Live Attendance System")

    if st.button("Take Attendance"):
        known_faces, known_names = load_known_faces()
        if not known_faces:
            st.warning("No registered faces found. Please register students first.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        frame_placeholder = st.empty()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Failed to access camera. Please check camera connection.")
            return

        recognition_count.clear()  # Reset recognition counts at the start

        try:
            start_time = datetime.now()
            while (datetime.now() - start_time).seconds < CAMERA_DURATION:
                progress = int(((datetime.now() - start_time).seconds / CAMERA_DURATION) * 100)
                progress_bar.progress(progress)
                status_text.text("Processing...")

                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to capture frame from camera")
                    break

                processed_frame, attendance_marked, recognized_names = process_frame(frame, known_faces, known_names)

                # ✅ Track how many times each name is recognized
                for name in recognized_names:
                    recognition_count[name] = recognition_count.get(name, 0) + 1

                frame_placeholder.image(processed_frame, channels="BGR")

            # ✅ Determine the most consistently recognized face
            most_recognized_name = max(
                recognition_count, key=recognition_count.get, default=None
            )

            # ✅ Only mark attendance if seen in at least MIN_REQUIRED_FRAMES frames
            if most_recognized_name and recognition_count[most_recognized_name] >= MIN_REQUIRED_FRAMES:
                mark_attendance(most_recognized_name)
                status_text.success(f"Attendance marked successfully for: {most_recognized_name}")
                playsound(SUCCESS_SOUND)
            else:
                status_text.warning("No faces recognized!")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            progress_bar.empty()
            frame_placeholder.empty()


def main():
    """Main function to run the attendance system"""
    st.set_page_config(page_title="Take Attendance", layout="wide")
    st.title("Take Attendance")
    
    # Insert default attendance records for the day
    # insert_default_attendance()
    
    # Run the attendance system
    take_attendance()

if __name__ == "__main__":
    main()