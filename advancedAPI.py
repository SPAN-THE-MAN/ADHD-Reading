import pytesseract
import tkinter
from tkinter import *
from tkinter import font
import customtkinter as ctk
from tkinter import messagebox
from pynput.keyboard import Key, Controller
from PIL import ImageGrab
from PIL import ImageTk
import time
from pathlib import Path
from pynput import mouse
from pynput.mouse import Button as mouseButton
import zmq
from flask import Flask
import requests
import datetime
from typing import Any
import subprocess

from sympy.codegen.ast import continue_

running = False
screenshotting = False
key_Controller = Controller()
bookmark = 0

class TextList:
    def __init__(self):
        self.words = []

    def append(self, word):
        self.words.append(word)

    def clear(self):
        self.words = []

    def word_count(self):
        return len(self.words)


    # More efficient to include this, only commenting out
    # to meet assignment instructions and force myself to use Text_Chunking_Service  (which is useless in reality)
    # def word_split(self, text):
    #     self.words = [w for w in text.split() if w]

text_list = TextList()


def kill_servers():
    # Kills OCR Text Scrape microservice.
    socket.send_string('Q')
    print("OCR terminated...")

    # Kills Search Feature microservice.
    data = {"kill": True}
    MICROSERVICE_URL = "http://127.0.0.1:8001/search"

    # Kill Search Feature
    # Send kill command; ignore response
    try:
        requests.post(MICROSERVICE_URL, json=data, timeout=0.5)
    except requests.exceptions.RequestException:
        pass  # ignore any errors since we don't care about the response
    print("Search terminated...")

    MICROSERVICE_URL = "http://127.0.0.1:8002/upload"
    # Kill File Upload
    # Send kill command; ignore response
    try:
        requests.post(MICROSERVICE_URL, json=data, timeout=0.5)
    except requests.exceptions.RequestException:
        pass  # ignore any errors since we don't care about the response
    print("Search terminated...")

    MICROSERVICE_URL = "http://127.0.0.1:8003/chunk"
    # Kill Text Chunking
    # Send kill command; ignore response
    try:
        requests.post(MICROSERVICE_URL, json=data, timeout=0.5)
    except requests.exceptions.RequestException:
        pass  # ignore any errors since we don't care about the response
    print("Chunking terminated...")

    return None

def ocr_scrape(filename=None):
    # Send request to OCR Text Scrape microservice

    socket.setsockopt(zmq.RCVTIMEO, 1000)
    if filename is None:
        socket.send_string('scrape')
    else:
        socket.send_string(filename)


    # Blocking. Receive output from OCR Text Scrape microservice.
    try:
        text = socket.recv()
    except:
        print("ERROR: ocr_scrape func. Scrape failed")


    return text

def chunk_text(text):
    data = {"contents": text}
    print("Sending request to Chunking Service...")
    response = requests.post("http://127.0.0.1:8003/chunk", json=data)
    return response.json()

def parse_text(text):
    global text_list


    text = text.replace('\n', ' ')
    text = text.replace('|', 'I')


    response = chunk_text(text)
    for chunk in response:
        text_list.append(chunk)

    print(text_list.words)

    print(f"Corrected text:\n{text}")
    print(text_list.words)
    print(f"Approx words: {text_list.word_count()}")
    return text_list.words

def error_window(error):
    pass



def handle_gui():
    print("Starting gui")
    window = Tk()
    window.minsize(500, 90)

    #Original: 840x840
    window.geometry('700x360')
    window.title('SPEED READER')


    # Create OCR resource directory if non-existent
    folder = Path(fr"microservices/Ocr Resource")
    if folder.exists():
        print("Success: OCR Resource folder found")
    else:
        print("Error: OCR Resource folder not found")

    def display_word(index):
        global bookmark
        word = text_list.words[index]
        label.config(text=word)
        bookmark = index
        slider.set(bookmark + 1)
        label_slider.config(text=bookmark + 1)

        delay = 200
        endings = ('.', ',', ';', '?', '!', '...')
        if natural_cadence_var.get() and word.endswith(endings):
            delay = 500
            print(f"Pausing on word '{word}'")
        return delay

    def run_reader():
        global bookmark, running
        if running and bookmark < text_list.word_count():
            # print(bookmark)
            delay = display_word(bookmark)
            bookmark += 1
            window.after(delay, run_reader)
        elif bookmark >= text_list.word_count():
            bookmark = 0
            label.config(text="END TEXT")
            running = False
            button_start_stop.config(text="Start")
            print("Stopped")
            status.config(text="Stopped")

    def button_start_stop():
        global running

        running = not running
        if running:
            button_start_stop.config(text="Stop")
            status.config(text="Running...")
            run_reader()

        else:
            button_start_stop.config(text="Start")
            status.config(text="Stopped")

    def screenshot():
        global screenshotting


        screenshot_img_name = "img.png"

        screenshotting = not screenshotting

        print('Taking screenshot...')
        key_Controller.press(Key.print_screen)
        key_Controller.release(Key.print_screen)

        start_posx = 0
        start_posy = 0

        def on_click(x, y, button, pressed):
            global start_posx, start_posy
            if button == mouseButton.left:
                if pressed:
                    # print(f'Pressing at x:{x} and y:{y}')
                    start_posx = x
                    start_posy = y
                    pass
                else:
                    # print(f'Left  releasing at x:{x} and y:{y}')
                    end_posx = x
                    end_posy = y
                    moved = False
                    if start_posx != end_posx and start_posy != end_posy:
                        # print(start_posx, start_posy)
                        # print(end_posx, end_posy)
                        return False

        # Collect events until released
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        time.sleep(1)

        confirm_screenshot = messagebox.askyesno("Load Screenshot",
                                            "Are you sure you want to load this screenshot?")
        if confirm_screenshot:
            print("Saving clipboard...")
            screenshot = ImageGrab.grabclipboard()
            screenshot.save(fr"microservices/OCR Resource/{screenshot_img_name}")
            print("Loading text...")

            #OCR TEXT SCRAPE MICROSERVICE HERE:
            text = ocr_scrape('scrape').decode()



            print("Microservice response received!")
            print(f"THIS IS THE TEXT: \n{text}")
            parse_text(text)
            label.config(text="Screenshot Loaded!")
        else:
            print("Cancelling screenshot load...")
            pass


        #By this point, image is loaded into app, text parsed, and ready to go.
        slider.configure(from_=1,
                         to=text_list.word_count(),
                         state="normal")

    def sliding(value):
        # Slider tutorial
        # https://www.youtube.com/watch?v=SiOVaR2ve_M
        value = int(value)
        global bookmark
        label_slider.config(text=int(value))
        bookmark = value - 1
        label.config(text=text_list.words[bookmark])

    def clear_and_reset():
        global text_list
        confirm_reset = messagebox.askyesno("Reset",
        "Are you sure you want to clear and reset?\n\nThis action cannot be undone.")
        if confirm_reset:
            print("Clearing and resetting...")
            status.config(text="Press start/stop to begin...")
            label.config(text="Take and use screenshot to start!")
            button_start_stop.config(text="Start/Stop")
            slider.configure(from_=0,
                             to=1,
                             state="disabled")
            label_slider.config(text="0")
            text_list.clear()
        else:
            print("Cancelling reset...")
            pass

    def upload_image():
        global bookmark
        print("Uploading image...")
        fileTypes = [("Image files", "*.png;*.jpg;*.jpeg")]
        path = tkinter.filedialog.askopenfilename(filetypes=fileTypes)
        if path == "":
            # User has canceled upload action, resume normally.
            print("Upload canceled...")
            return None
        else:
            try:
                print("taking try path")
                text = ocr_scrape(path).decode()
                print("\nOCR extraction successful!\n")
                print(f"OCR INTERPRETATION:\n{text}")

            except Exception as error:
                print(f'ERROR: {error}')

                error = f'{error}. (error code: 100)'
                messagebox.showerror("Error", f"{error}")
                return None

        parse_text(text)
        bookmark = 0
        label.config(text="Image Loaded!")

        # By this point, image is loaded into app, text parsed, and ready to go.
        slider.configure(from_=1,
                         to=text_list.word_count(),
                         state="normal")
        return None

    def show_slider():

        # Ensures that when in reader mode, show slider button remains unaffected.
        if not reader_mode_var.get():
            if show_slider_var.get():
                show_slider_var.set(False)
            else:
                show_slider_var.set(True)
            return
        print(show_slider_var.get())
        if show_slider_var.get():
            print("Showing slider!")
            slider.grid(row=4, column=0, pady=(10,0))
            label_slider.grid(row=5, column=0, pady=10)
        elif not show_slider_var.get():
            print("Not showing slider!")
            slider.grid_forget()
            label_slider.grid_forget()
        else:
            print("BROKEN!")

    def search():
        global text_list
        word = search_entry.get()
        if word == '':
            return None
        else:
            print(f"Searching for '{word}'...")
            MICROSERVICE_URL = "http://127.0.0.1:8001/search"

            data: dict[str, Any] = {
                "data_source": text_list.words,
                "query": word,
                "strict": None,
                "file_lookup": None
            }

            results = requests.post(MICROSERVICE_URL, json=data).json()
            search_term = results["search_term"]
            if len(results) == 1:
                print(f"Results: Item not found.")
                search_results_label.config(text=f"0 reference(s) found for '{results["search_term"]}'")
                search_results_label.pack(side="left", padx=5)
                return None

            print(f"Results: {results}")

            count = results["count"]
            first_index = results["first_index"]

            search_results_label.config(text=f"{count} reference(s) found for '{search_term}'")
            search_results_label.pack(side="left", padx=5)

            display_word(first_index)

            return None

    def switch_mode_to_notes():
        reader_mode_var.set(False)
        print("Switching to notes mode...")
        window.geometry('700x500')

        # Hide all non-notes mode-related widgets
        status.grid_forget()
        label.grid_forget()
        button_start_stop.grid_forget()
        slider.grid_forget()
        label_slider.grid_forget()
        toolbar.grid_forget()

        # Show all notes mode-related widgets
        notes_textbox.grid(row=0, column=0, pady=10)

        menu_notes = tkinter.Menu(menu, tearoff=False)

        menu_notes.add_command(label="Upload", command=upload_file)
        menu_notes.add_command(label="Download", command=download_file)
        menu.add_cascade(label="Notes", menu=menu_notes)

        window.config(menu=menu)

        return None

    def switch_mode_to_reader():
        reader_mode_var.set(True)
        print("Switching to reader mode...")


        # Hide all non-reader mode-related widgets
        notes_textbox.grid_forget()
        try:
            menu.delete("Notes")
        except:
            pass

        # Show all reader mode-related widgets
        status.grid(row=1, column=0, pady=10)
        label.grid(row=2, column=0, pady=10)
        button_start_stop.grid(row=3, column=0, pady=10)
        toolbar.grid(row=0, column=0, sticky="ew")

        if show_slider_var.get():
            slider.grid(row=4, column=0, pady=(10, 0))
            label_slider.grid(row=5, column=0, pady=10)

        return None

    def upload_file():
        print("Uploading file...")

        content = notes_textbox.get("1.0", tkinter.END)
        print(f"Content: {content}")

        path = tkinter.filedialog.asksaveasfilename(
            defaultextension=".txt",  # optional default file extension
            filetypes=[("Text and JSON files", "*.txt; *json")],  # filters
            initialdir=fr"microservices/Notes",  # starting folder
            title="Save your file"  # dialog title
        )


        print(f"Path: {path}")

        data = {"filepath": path, "file_contents": content}
        results = call_upload_file_service(data)
        print(results)

        return None

    def download_file():
        fileTypes = [("Text and JSON files", "*.txt;*.json")]
        path = tkinter.filedialog.askopenfilename(initialdir=fr"microservices/Notes",filetypes=fileTypes)
        if path == "":
            # User has canceled upload action, resume normally.
            print("Download canceled...")
            return None
        else:
            with open(fr"{path}", "r") as f:
                content = f.read()

            # Overwrite current notes with downloaded notes.
            notes_textbox.delete("1.0", tkinter.END)
            notes_textbox.insert("1.0", content)  # Insert into a Text widget
            return None

    def call_upload_file_service(data: dict[str, Any]):
        response = requests.post("http://127.0.0.1:8002/upload", json=data)
        return response.json()


    # Creates icon for window
    icon = PhotoImage(file=fr'gui resources/pokeball_icon.png')
    window.iconphoto(True, icon)
    window.config(background='purple')
    window.grid_columnconfigure(0, weight=1)

    font = tkinter.font.Font(size=25)

    notes_textbox = tkinter.Text(window)
    notes_textbox.grid(row=0, column=0, pady=10)
    notes_textbox.grid_forget()

    #Status label
    status = Label(window,
                   anchor="center",
                   text="Press start/stop to begin...")
    status.grid(row=1, column=0, pady=10)

    #Print screen label (prints words one at a time)
    label = Label(window,
                  anchor="center",
                  text="Take and use screenshot to start!",
                  font=font,
                  fg='black',
                  height=3,
                  width=25
    )
    label.grid(row=2, column=0, pady=10)


    #Start/Stop button
    button_start_stop = Button(window,
                    text="Start/Stop",
                    anchor="center",
                    command=button_start_stop,
                    height=3,
                    width=13
    )
    button_start_stop.grid(row=3, column=0, pady=10)



    #Progress slider
    slider = ctk.CTkSlider(window,
                           from_=0,
                           to=1,
                           command=sliding
                           )
    slider.grid(row=4, column=0, pady=(10,0))
    slider.configure(state="disabled")
    slider.set(0)
    slider.grid_forget()

    #Label for slider (Tracks current word position)
    label_slider = Label(window,
                  anchor="center",
                  text=slider.get(),
                  fg='black',
                  height=1,
                  width=5
    )
    label_slider.grid(row=5, column=0, pady=10)
    label_slider.grid_forget()





    #Tutorial for menu https://www.youtube.com/watch?v=aODNQnc4Ebc
    #menu
    menu = tkinter.Menu(window)
    show_slider_var = tkinter.BooleanVar()
    show_slider_var.set(False)

    reader_mode_var = tkinter.BooleanVar()
    reader_mode_var.set(True)

    natural_cadence_var = tkinter.BooleanVar()
    natural_cadence_var.set(False)


    #sub menu - file tab
    menu_file = tkinter.Menu(menu, tearoff=False)

    menu_file.add_command(label='Upload image', command=upload_image)
    menu_file.add_command(label='Clear and reset', command=clear_and_reset)
    menu_file.add_command(label='Take screenshot', command=screenshot)
    menu_file.add_checkbutton(label = 'Show slider', command=show_slider, variable=show_slider_var)

    menu.add_cascade(label='File', menu=menu_file)


    # sub menu - mode tab
    menu_mode = tkinter.Menu(menu, tearoff=False)

    menu_mode.add_command(label="Notes", command=switch_mode_to_notes)
    menu_mode.add_command(label="Speed Reader", command=switch_mode_to_reader)
    menu_mode.add_checkbutton(label = 'Natural cadence', variable=natural_cadence_var)
    menu.add_cascade(label="Modes", menu=menu_mode)

    window.config(menu=menu)

    toolbar = tkinter.Frame(window)
    toolbar.grid(row=0, column=0, sticky="ew")  # stretch across top

    button_search = Button(toolbar, text="Search", command=search)
    button_search.pack(side="left", padx=5)

    search_entry = tkinter.Entry(toolbar, width=25)
    search_entry.pack(side="left", padx=5)

    search_results_label = tkinter.Label(toolbar, text="'' reference(s) found for ''")
    search_results_label.pack(side="left", padx=5)
    search_results_label.pack_forget()




    #Builds and keeps the GUI running
    window.mainloop()
    print("Gui has been stopped")

# Buggy code
# Command prompt commands:
# List running py scripts: tasklist /FI "IMAGENAME eq python.exe"
# Kill running py scripts: taskkill /F /IM python.exe
"""
def start_microservices():
    microservices = [
        fr"microservices/OCR_Text_Scrape_Service.py",
        fr"microservices/Search_Feature_Service.py",
        fr"microservices/File_Upload_Service.py"
    ]

    # Tracks running processes, can be used later to shut down.
    processes = []

    # Starts each py file in 'microservices'.
    for microservice in microservices:
        p = subprocess.Popen(["python", microservice])
        processes.append(p)
"""



if __name__ == "__main__":
    context = zmq.Context()
    print("Client attempting to connect to server...")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    app = Flask(__name__)

    # start_microservices()

    handle_gui()
    kill_servers()
