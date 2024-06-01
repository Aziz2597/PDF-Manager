from flask import Flask, request, send_file, render_template
import os
import img2pdf
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the download folder
DOWNLOAD_FOLDER = r"C:\Users\azizu\Downloads"

def save_file(output_stream, filename):
    output_path = os.path.join(DOWNLOAD_FOLDER, filename)
    with open(output_path, "wb") as output_file:
        output_file.write(output_stream.getbuffer())
    return output_path

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/merge", methods=["GET", "POST"])
def merge_pdfs():
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files:
            return render_template("merge.html", error="No files uploaded")

        merger = PdfMerger()
        for file in files:
            merger.append(BytesIO(file.read()))

        output_stream = BytesIO()
        merger.write(output_stream)
        merger.close()
        output_stream.seek(0)

        filename = secure_filename(request.form["filename"] + ".pdf")
        return send_file(output_stream, as_attachment=True, download_name=filename)
    return render_template("merge.html")

@app.route("/split", methods=["GET", "POST"])
def split_pdf():
    if request.method == "POST":
        file = request.files["file"]
        start_page1 = int(request.form["start_page1"])
        start_page2 = int(request.form["start_page2"])
        filename1 = (request.form["filename1"] + ".pdf")  
        filename2 = (request.form["filename2"] + ".pdf")  

        pdf_reader = PdfReader(file)
        if start_page1 <= 0 or start_page2 <= 0 or start_page1 >= start_page2:
            return render_template("split.html", error="Invalid page range")

        pdf_writer1 = PdfWriter()
        for page in range(start_page1 - 1, start_page2 - 1):
            pdf_writer1.add_page(pdf_reader.pages[page])
        output_stream1 = BytesIO()
        pdf_writer1.write(output_stream1)
        output_stream1.seek(0)
        save_file(output_stream1, filename1)

        pdf_writer2 = PdfWriter()
        for page in range(start_page2 - 1, len(pdf_reader.pages)):
            pdf_writer2.add_page(pdf_reader.pages[page])
        output_stream2 = BytesIO()
        pdf_writer2.write(output_stream2)
        output_stream2.seek(0)
        save_file(output_stream2, filename2)

        return "PDF Split Successful!"

    return render_template("split.html")

@app.route("/encrypt", methods=["GET", "POST"])
def encrypt_pdf():
    if request.method == "POST":
        file = request.files["file"]
        password = request.form["password"]

        if not password:
            return render_template("encrypt.html", error="Please provide a password.")

        pdf_reader = PdfReader(file)
        pdf_writer = PdfWriter()
        for page_num in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        pdf_writer.encrypt(password)

        output_stream = BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        filename = secure_filename(file.filename.split(".")[0] + "_encrypted.pdf")
        return send_file(output_stream, as_attachment=True, download_name=filename)
    return render_template("encrypt.html")

@app.route("/extract", methods=["GET", "POST"])
def extract_text():
    if request.method == "POST":
        file = request.files["file"]
        pdf_reader = PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()

        if not text:
            return render_template("extract.html", error="No text found in PDF")

        output_stream = BytesIO()
        output_stream.write(text.encode("utf-8"))
        output_stream.seek(0)
        original_filename = secure_filename(file.filename)
        filename = original_filename.split(".")[0] + "_extracted.txt"
        return send_file(output_stream, as_attachment=True, download_name=filename)
    return render_template("extract.html")

@app.route("/image_to_pdf", methods=["GET", "POST"])
def image_to_pdf():
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files:
            return render_template("image_to_pdf.html", error="No files uploaded")

        filename = secure_filename(request.form["filename"] + ".pdf")
        images = [file.read() for file in files]

        output_stream = BytesIO()
        try:
            output_stream.write(img2pdf.convert(images))
            output_stream.seek(0)
        except Exception as e:
            return render_template("image_to_pdf.html", error="Error converting images to PDF: " + str(e))

        return send_file(output_stream, as_attachment=True, download_name=filename)
    return render_template("image_to_pdf.html")

@app.route("/unlock_pdf", methods=["GET", "POST"])
def unlock_pdf():
    if request.method == "POST":
        file = request.files["file"]
        password = request.form["password"]

        if not password:
            return render_template("unlock.html", error="Please provide a password.")

        original_filename = secure_filename(file.filename)
        filename = original_filename.split(".")[0] + "_unlocked.pdf"

        input_path = os.path.join(DOWNLOAD_FOLDER, secure_filename(file.filename))
        output_path = os.path.join(DOWNLOAD_FOLDER, filename)

        file.save(input_path)
        file.close()  # Close the input file after saving

        reader = PdfReader(input_path)
        if reader.is_encrypted:
            try:
                reader.decrypt(password)
            except Exception as e:
                return render_template("unlock.html", error="Error unlocking PDF: " + str(e))

        writer = PdfWriter()
        for page_num in range(len(reader.pages)):
            writer.add_page(reader.pages[page_num])

        output_stream = BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)

        return send_file(output_stream, as_attachment=True, download_name=filename)
    return render_template("unlock.html")

if __name__ == "__main__":
    app.run(debug=True)
