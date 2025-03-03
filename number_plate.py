import cv2
import pytesseract
import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
from threading import Thread
import easyocr
import re

# Path configurations
harcascade = r"C:\Users\harsh\OneDrive\Documents\College\Python\PDEA\Capstone Project\Capstone Project\model\haarcascade_russian_plate_number.xml"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Database connection
conn = sqlite3.connect("vehicle_data.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS vehicle_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_text TEXT UNIQUE,
                    entry_time TEXT,
                    exit_time TEXT,
                    duration REAL,
                    bill REAL)''')
conn.commit()

# Function to calculate the bill based on entry and exit time
def calculate_bill(entry_time, exit_time):
    rate_per_hour = 50.0  # Rate per hour
    duration = (exit_time - entry_time).total_seconds() / 3600
    bill = round(duration * rate_per_hour, 2)
    return duration, bill

# Refresh table to show the latest data from the database
def refresh_table():
    """Refresh the table in the GUI with the latest data from the database."""
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT plate_text, entry_time, exit_time, duration, bill FROM vehicle_log")
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)

# Function to process vehicle exit and generate the bill
def process_exit():
    """Process vehicle exit by updating exit time and calculating the bill."""
    plate_number = plate_entry.get().strip()  # Get plate number from entry field
    if not plate_number:
        messagebox.showerror("Error", "Enter a valid plate number")
        return

    cursor.execute("SELECT * FROM vehicle_log WHERE plate_text = ? AND exit_time IS NULL", (plate_number,))
    record = cursor.fetchone()

    if record:
        entry_time = datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.now()
        duration, bill = calculate_bill(entry_time, exit_time)

        cursor.execute("""UPDATE vehicle_log
                          SET exit_time = ?, duration = ?, bill = ?
                          WHERE id = ?""",
                       (exit_time.strftime("%Y-%m-%d %H:%M:%S"), duration, bill, record[0]))
        conn.commit()

        messagebox.showinfo("Success", f"Bill Generated\nPlate: {plate_number}\nDuration: {duration:.2f} hrs\nBill: ₹{bill:.2f}")
        refresh_table()
    else:
        messagebox.showerror("Error", "Vehicle not found or already exited")

# Function to clear the entry field
def clear_entries():
    """Clear the input entry field."""
    plate_entry.delete(0, END)

# Function to clear all records from the database
def clear_all_records():
    """Delete all records from the database and refresh the table."""
    confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete all records?")
    if confirm:
        cursor.execute("DELETE FROM vehicle_log")
        conn.commit()
        refresh_table()
        messagebox.showinfo("Success", "All records cleared successfully!")

# Function to select a record from the table and populate the entry field
def on_record_select(event):
    """Fetch selected record's plate number and populate the entry field."""
    selected_item = tree.selection()
    if selected_item:
        record = tree.item(selected_item, "values")
        plate_entry.delete(0, END)  # Clear the entry field
        plate_entry.insert(0, record[0])  # Populate it with the plate number

# Function to manually add a plate
def manually_add_plate():
    plate_number = plate_entry.get().strip()
    if not plate_number:
        messagebox.showerror("Error", "Enter a valid plate number")
        return

    cursor.execute("SELECT * FROM vehicle_log WHERE plate_text = ? AND exit_time IS NULL", (plate_number,))
    record = cursor.fetchone()

    if record:
        # If the vehicle is already in the system and has not exited yet
        entry_time = datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S")
        exit_time = datetime.now()
        duration, bill = calculate_bill(entry_time, exit_time)

        # Mark the previous entry as exited
        cursor.execute("""UPDATE vehicle_log
                          SET exit_time = ?, duration = ?, bill = ?
                          WHERE id = ?""",
                       (exit_time.strftime("%Y-%m-%d %H:%M:%S"), duration, bill, record[0]))
        conn.commit()

        messagebox.showinfo("Success", f"Duplicate plate detected. Previous record for {plate_number} marked as exited.\n"
                                      f"Exit Time: {exit_time}\nDuration: {duration:.2f} hrs\nBill: ₹{bill:.2f}")
        refresh_table()
    else:
        # If no active record is found, add a new entry
        entry_time = datetime.now()
        try:
            cursor.execute("INSERT INTO vehicle_log (plate_text, entry_time) VALUES (?, ?)", 
                           (plate_number, entry_time.strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            messagebox.showinfo("Success", f"Vehicle {plate_number} added with entry time {entry_time}")
            refresh_table()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Duplicate entry detected for plate: {plate_number}")

# Preprocessing functions for OCR accuracy
def preprocess_plate(img_roi):
    """Preprocess the detected plate image."""
    img_gray = cv2.cvtColor(img_roi, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    img_thresh = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    img_resized = cv2.resize(img_thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return img_resized

# Function to filter valid plate text (only alphanumeric characters)
def filter_plate_text(plate_text):
    """Filter out invalid characters from the plate text."""
    # Using regular expression to keep only alphanumeric characters (A-Z, a-z, 0-9, space)
    valid_plate_text = re.sub(r'[^a-zA-Z0-9\s]', '', plate_text)
    return valid_plate_text.strip()

# OCR function using both EasyOCR and Tesseract
def get_plate_text(img_roi):
    """Extract plate text using EasyOCR and Tesseract."""
    # Preprocess image for better accuracy
    img_preprocessed = preprocess_plate(img_roi)

    # EasyOCR
    reader = easyocr.Reader(['en'], gpu=True)
    plate_text_easyocr = reader.readtext(img_preprocessed, detail=0, paragraph=False)

    if plate_text_easyocr:
        plate_text = plate_text_easyocr[0]  # Return first result from EasyOCR
        # Filter the plate text to include only alphanumeric characters
        plate_text = filter_plate_text(plate_text)
        return plate_text

    # If EasyOCR failed, fall back to Tesseract
    custom_config = r'--oem 3 --psm 6'
    plate_text_tesseract = pytesseract.image_to_string(img_preprocessed, config=custom_config)
    
    # Filter the plate text to include only alphanumeric characters
    plate_text_tesseract = filter_plate_text(plate_text_tesseract)
    
    return plate_text_tesseract.strip()

# Function to run the plate scanning in a separate thread
def scan_plates():
    """Run number plate detection using OpenCV with user-controlled capture."""
    # Create a separate database connection for this thread
    thread_conn = sqlite3.connect("vehicle_data.db")
    thread_cursor = thread_conn.cursor()

    plate_cascade = cv2.CascadeClassifier(harcascade)
    if plate_cascade.empty():
        print("Error loading cascade classifier")
        return

    cap = cv2.VideoCapture(0)  # Open webcam

    last_detected_plate = None
    detection_count = 0

    while True:
        success, img = cap.read()
        if not success:
            break

        # Convert to grayscale
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect plates
        plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)

        for (x, y, w, h) in plates:
            aspect_ratio = w / h
            area = w * h
            if 2 <= aspect_ratio <= 5 and area > 1000:  # Typical license plate aspect ratio
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                img_roi = img[y:y + h, x:x + w]

                # Show the detected plates on the video feed
                cv2.imshow("Plate Detection", img)

                # Wait for user to press 'g' to capture
                key = cv2.waitKey(1) & 0xFF
                if key == ord('g'):
                    print("User triggered capture")

                    # Get plate text using OCR
                    plate_text = get_plate_text(img_roi)

                    if plate_text:
                        print("Detected Plate:", plate_text)

                        # Check for exit condition (plate detected twice)
                        if plate_text == last_detected_plate:
                            detection_count += 1
                        else:
                            last_detected_plate = plate_text
                            detection_count = 1

                        # Handle the case when plate is detected twice in a short time
                        if detection_count == 2:
                            thread_cursor.execute(
                                "SELECT * FROM vehicle_log WHERE plate_text = ? AND exit_time IS NULL",
                                (plate_text,))
                            record = thread_cursor.fetchone()

                            if record:
                                entry_time = datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S")
                                exit_time = datetime.now()
                                duration, bill = calculate_bill(entry_time, exit_time)

                                thread_cursor.execute("""UPDATE vehicle_log
                                                         SET exit_time = ?, duration = ?, bill = ?
                                                         WHERE id = ?""",
                                                      (exit_time.strftime("%Y-%m-%d %H:%M:%S"), duration, bill, record[0]))
                                thread_conn.commit()

                                print(f"Vehicle {plate_text} exiting at {exit_time}. Bill generated: ₹{bill:.2f}")
                                # Reset detection count after processing exit
                                detection_count = 0

                            else:
                                print(f"Plate {plate_text} not found in active vehicles.")

                        # If the plate is not already in the database, add it with the current entry time
                        if detection_count == 1:
                            thread_cursor.execute(
                                "SELECT * FROM vehicle_log WHERE plate_text = ? AND exit_time IS NULL", (plate_text,))
                            record = thread_cursor.fetchone()

                            if not record:
                                entry_time = datetime.now()
                                try:
                                    thread_cursor.execute(
                                        "INSERT INTO vehicle_log (plate_text, entry_time) VALUES (?, ?)",
                                        (plate_text, entry_time.strftime("%Y-%m-%d %H:%M:%S"))
                                    )
                                    thread_conn.commit()
                                    print(f"Vehicle {plate_text} entered at {entry_time}")
                                except sqlite3.IntegrityError:
                                    print(f"Duplicate entry detected for plate: {plate_text}")

                        # Refresh the GUI table from the main thread
                        root.after(0, refresh_table)

        # Display the video feed
        cv2.imshow("Plate Detection", img)

        # Exit if the user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Close the thread's database connection
    thread_conn.close()
    cap.release()
    cv2.destroyAllWindows()

# GUI with Tkinter
root = Tk()
root.title("Vehicle Billing System")
root.geometry("900x600")

# Title
Label(root, text="Vehicle Billing System", font=("Helvetica", 16, "bold")).pack(pady=20)

# Entry Frame
frame = Frame(root)
frame.pack(pady=10)

Label(frame, text="Enter Plate Number:", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=5)
plate_entry = Entry(frame, font=("Helvetica", 12), width=20)
plate_entry.grid(row=0, column=1, padx=10, pady=5)

exit_button = Button(frame, text="Process Exit", font=("Helvetica", 12), command=process_exit, bg="green", fg="white")
exit_button.grid(row=0, column=2, padx=10, pady=5)

clear_button = Button(frame, text="Clear", font=("Helvetica", 12), command=clear_entries, bg="red", fg="white")
clear_button.grid(row=0, column=3, padx=10, pady=5)

clear_all_button = Button(frame, text="Clear All Records", font=("Helvetica", 12), command=clear_all_records, bg="orange", fg="white")
clear_all_button.grid(row=0, column=4, padx=10, pady=5)

# Button to manually add a plate
manual_add_button = Button(frame, text="Manually Add Plate", font=("Helvetica", 12), command=manually_add_plate, bg="blue", fg="white")
manual_add_button.grid(row=1, column=1, padx=10, pady=5)

# Data Table
columns = ("Plate Number", "Entry Time", "Exit Time", "Duration (hrs)", "Bill (₹)")
tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
tree.pack(pady=20, fill=BOTH, expand=True)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor=CENTER)

# Bind record selection to on_record_select
tree.bind("<<TreeviewSelect>>", on_record_select)

# Refresh Button
refresh_button = Button(root, text="Refresh Table", font=("Helvetica", 12), command=refresh_table, bg="blue", fg="white")
refresh_button.pack(pady=20)

# Start the plate scanning thread
thread = Thread(target=scan_plates, daemon=True)
thread.start()

root.mainloop()
