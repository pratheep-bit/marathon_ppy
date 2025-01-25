from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import sqlite3
import os

app = Flask(__name__)

# Database setup
DB_PATH = 'participants.db'  # Your SQLite database file path

# Directories for saving files
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Database helper function to get participant name and distance by chest card number
def get_name_by_card_number(chest_card_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, distance FROM participants WHERE chest_card_number=?", (chest_card_number,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_certificate', methods=['POST'])
def generate_certificate():
    # Get inputs
    chest_card_number = request.form.get('chest_card_number')
    photo = request.files.get('photo')

    if not chest_card_number or not photo:
        return "Error: Missing chest card number or photo!", 400

    # Check if the card number is valid and get details
    name, distance = get_name_by_card_number(chest_card_number)
    if not name:
        return "Invalid chest card number.", 400
    

    # Save the uploaded photo
    try:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        photo.save(photo_path)

        # Ensure the file is a valid image
        with Image.open(photo_path) as img:
            img.verify()  # Check if the file is an image
    except Exception as e:
        return f"Error: Uploaded file is not a valid image. Details: {e}", 400

    # Generate the certificate
    try:
        certificate_path = create_certificate_image(name, distance, photo_path)
    except Exception as e:
        return f"Error during certificate creation: {e}", 500

    # Redirect to download the certificate
    return redirect(url_for('download_certificate', filename=os.path.basename(certificate_path)))

def create_certificate_image(name, distance, photo_path):
    # Path to the certificate template
    template_path = 'static/certificate_template.jpg'  # Update with your actual path

    # Open the certificate template
    template_image = Image.open(template_path)
    
    # Resize the uploaded photo
    photo = Image.open(photo_path)
    photo_width = 286 + 30  # Width of the photo
    photo_height = 371 + 30  # Height of the photo
    photo = photo.resize((photo_width, photo_height))  # Resize the photo
    
    # Adjust photo position
    photo_position = (446, 410)
    template_image.paste(photo, photo_position)  # Paste the photo on the template
    
    # Set up drawing context
    draw = ImageDraw.Draw(template_image)

    # Load fonts
    font_size_name = 75
    font_size_distance = 75  # Smaller font for distance
    try:
        font_name = ImageFont.truetype("static/newf.ttf", font_size_name)
        font_distance = ImageFont.truetype("static/newf.ttf", font_size_distance)
    except IOError:
        font_name = font_distance = ImageFont.load_default()

    # Positions for the name and distance
    name_position = (320, 1280)  # Adjust as needed for name
    distance_position = (2370, 1280)  # Adjust as needed for distance

    # Draw the name and distance on the certificate
    draw.text(name_position, name, font=font_name, fill="#3c3277")  # Use your preferred text color
    # Extract only the numeric part from the distance (e.g., '3' from '3 km')
    numeric_distance = ''.join(filter(str.isdigit, distance))
    draw.text(distance_position, numeric_distance, font=font_distance, fill="#3c3277")



    # Save the certificate as a new image file
    output_path = os.path.join(GENERATED_FOLDER, 'certificate_generated.png')
    template_image.save(output_path)

    return output_path

@app.route('/download_certificate/<filename>')
def download_certificate(filename):
    # Serve the certificate from the correct folder
    return send_from_directory(app.config['GENERATED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=8000)

