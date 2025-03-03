# Smart-Parking-System
Smart Parking System Using Opencv
# Features:
- Real-time vehicle number plate detection using a webcam.
- OCR (Optical Character Recognition) to extract plate text using both EasyOCR and Tesseract.
- Entry and exit logging of vehicles with automatic bill generation.
- Database for storing vehicle log data.
- GUI to interact with the system, including options for adding vehicles manually, processing exits, and refreshing the log.

# Technologies Used

- **Python**: The main programming language used for development.
- **OpenCV**: Used for detecting vehicle number plates from video feed captured via webcam.
- **Tesseract**: OCR engine used for recognizing vehicle number plate text.
- **EasyOCR**: Another OCR library used for text recognition, as a fallback if Tesseract doesn't work well.
- **SQLite**: A lightweight, serverless database to store vehicle logs.
- **Tkinter**: Python's standard GUI library to create the user interface.
- **Regular Expressions**: To filter valid vehicle plate text.
 
