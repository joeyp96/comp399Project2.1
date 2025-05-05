import PySimpleGUI as sg
import sqlite3
import os

# create the database if it doesn't exist
DB_FILE = "suggestions.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            suggestion_title TEXT NOT NULL,
            suggestion_description TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def open_feedback_window():
    layout = [
        [sg.Text("Your Name", size=(15, 1)), sg.Input(key="-NAME-")],
        [sg.Text("Suggestion Title", size=(15, 1)), sg.Input(key="-TITLE-")],
        [sg.Text("Description", size=(15, 1))],
        [sg.Multiline(size=(50, 10), key="-DESC-")],
        [sg.Push(), sg.Button("Submit Suggestion", button_color=("white", "green")),
         sg.Button("Cancel", button_color=("white", "firebrick"))]
    ]

    window = sg.Window("💡 Suggest a Feature", layout, modal=True)

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break
        elif event == "Submit Suggestion":
            name = values["-NAME-"].strip()
            title = values["-TITLE-"].strip()
            desc = values["-DESC-"].strip()

            if name and title and desc:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO suggestions (user_name, suggestion_title, suggestion_description) VALUES (?, "
                          "?, ?)",
                          (name, title, desc))
                conn.commit()
                conn.close()
                sg.popup_ok("Suggestion submitted successfully!", title="Thanks")
                break
            else:
                sg.popup_error("All fields must be filled out.", title="Missing Info")

    window.close()
