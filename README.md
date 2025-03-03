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
 
## Installation

1. Clone the repository:
[git clone https://github.com/yourusername/vehicle-billing-system.git cd vehicle-billing-system](https://github.com/harshal-0785/Smart-Parking-System)

2. Install the required Python libraries using `pip`:
pip install -r requirements.txt

3. Install Tesseract OCR:
- Windows: Download Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system's PATH.
- Mac: You can install Tesseract using Homebrew:
  ```
  brew install tesseract
  ```

4. Install EasyOCR:
pip install easyocr

5. Download the Haar Cascade XML file for number plate detection:
- You can use the Haar Cascade model from OpenCV's repository. Make sure to specify the correct path for it in the code.

6. Run the application:
python main.py

This will open the GUI, and the system will start detecting number plates and generating bills.

## Usage

- **Plate Detection**: Press 'g' on the video feed to capture a detected plate. If the plate is not already in the system, it will be logged. If it's already in the system, the exit process will be triggered, and a bill will be generated.
- **Process Exit**: Manually enter the plate number to process the exit and generate the parking bill.
- **Manually Add Plate**: You can manually enter a plate number and log its entry.
- **Clear All Records**: You can clear all vehicle records from the database.
- **Refresh**: Refresh the GUI table to show the latest data.

## Acknowledgements

- OpenCV for image processing and plate detection.
- Tesseract and EasyOCR for text recognition.
- Tkinter for building the GUI.
- SQLite for data storage.
