import zmq
import pytesseract
import cv2

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")


def deskew_image(image):
    """
    Purpose: Takes image, modifies resolution and other characteristics for higher OCR accuracy.
    Params: image - an image with text on it for the OCR to scrape from.
    Returns: gray - the same image tweaked for better text scraping
    """

    #Upscale image for readability.
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    #makes BGR(blue green red) image grayscale. Mss captures in BGR, so BGR is needed for processing.
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    img_gray_blur = cv2.GaussianBlur(img_gray, (5,5), 0)

    #Makes image black and white strictly (0=black, 255=white)
    _, img_blackwhite = cv2.threshold(img_gray_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)


    #calculate if there are more white or black pixels
    white_pixels_count = cv2.countNonZero(img_blackwhite)
    black_pixels_count = img_blackwhite.size - white_pixels_count

    #if more white, proceed normally.
    if white_pixels_count >= black_pixels_count:
        cv2.imwrite(fr"OCR Resource/processed_img.png", img_blackwhite)
        return img_blackwhite
    #if more black, invert image, then proceed.
    else:
        img_processed = cv2.bitwise_not(img_blackwhite)
        cv2.imwrite(fr"OCR Resource/processed_img.png", img_processed)
        return img_processed

def get_image(filename):
    """
    Purpose: Takes in filename, searches for image of said filename in Resource directory and validates it.
    Params: filename - a string, the name of the image to be scraped.
    Returns: image - an image object.
    """
    filepath = fr"{filename}"

    image = cv2.imread(filepath)
    if image is None:
        return f'ERROR: Could not read image: {filepath}'

    return image

def create_pdf(image):
    """
    Purpose: Takes image, and creates a PDF from it.
    Params: image - an image with text on it to be turned into PDF.
    Returns: None
    """
    # Get a searchable PDF
    pdf = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')

    try:
        with open(fr'microservices/OCR Resource/test.pdf', 'w+b') as f:
            f.write(pdf)  # pdf type is bytes by default
    except Exception as e:
        print("Could not create PDF")
        print(e)

    return None

def ocr_scrape(filename):
    """
    Purpose: Main function. Takes an image and scrapes text from it.
    Params: image - an image object to scrape text from.
    Returns: text - a string containing the text from the scraped image.
    """
    print("Starting OCR")

    image = get_image(filename)
    # Get a searchable PDF
    create_pdf(image)
    # Deskews image before OCR to improve text extraction on rotated scans/photos
    deskewed_image = deskew_image(image)

    # Timeout/terminate the tesseract job after a period of time
    try:
        text = pytesseract.image_to_string(deskewed_image, timeout=2)
        print("\nOCR extraction successful!\n")
        print(f"OCR INTERPRETATION:\n{text}")  # Timeout after 2 seconds
        return text

    except RuntimeError as timeout_error:
        # Tesseract processing is terminated
        print("timed out")
        print(timeout_error)
        return f'ERROR: {timeout_error}'

def main():
    while True:
        print('Running OCR')
        message = socket.recv()
        print(f"Received message: {message.decode()}")

        if len(message) > 0:
            if message.decode() == "Q":
                socket.send_string("Q")
                break

            elif message.decode() == "scrape":
                print("Scrape request received, scraping...")
                # Begin scraping
                text = ocr_scrape(fr"OCR Resource/img.png")

                print(f"Scrape successful, sending back text")
                socket.send_string(text)

            else:
                print("Upload option selected.")
                print("Scrape request received, scraping...")
                # Begin scraping
                text = ocr_scrape(message.decode())

                print(f"Scrape successful, sending back text")
                socket.send_string(text)

def test():
    print("Running OCR")
    text = ocr_scrape("OCR Resource/img.png")

if __name__ == "__main__":
    main()
    #test()