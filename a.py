import cv2

# Load the cascade for Russian number plates
plate_cascade = cv2.CascadeClassifier(
    r"C:\Users\BABLOO KUMAR\OneDrive\Desktop\Coding\Python\haarcascade_russian_plate_number.xml"
)

# Check if cascade loaded correctly
if plate_cascade.empty():
    print("Error: Cascade file not loaded. Check the path!")
    exit()

# Read the input image
img = cv2.imread("car.jpg")
if img is None:
    print("Error: Image not found. Check the path!")
    exit()

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Detect plates
plates = plate_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=4,
    minSize=(60, 20)
)

# Draw rectangles around detected plates
for (x, y, w, h) in plates:
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Show the result
cv2.imshow("Number Plate Detection", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Optional: Save the output
cv2.imwrite("detected_plate.jpg", img)
print("✅ Detection complete, saved as detected_plate.jpg")
