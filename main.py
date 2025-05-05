# project 2 joseph pignatone
import PySimpleGUI as sg
import os
import google.generativeai as genai
import simpleaudio as sa
# from huggingface_hub import InferenceClient (old import)
from audio_tools import detect_bpm, normalize_audio, remove_silence, apply_equalizer, bass_boost, apply_reverb, \
    reverse_audio, play_with_meter
from feedback import open_feedback_window

with open("secret.txt", "r", encoding="utf-8") as api_file:
    api_key = api_file.read().strip()

genai.configure(api_key=api_key)

# altered from python dictionary to resolve error
generation_config = genai.types.GenerationConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])


def query_llm(prompt: str) -> str:
    try:
        response = chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Gemini: {str(e)}"


play_obj = None  # controls audio playback


def play_audio(file_path):
    global play_obj
    try:
        if not file_path.lower().endswith(".wav"):
            return "Only .wav files can be played."

        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        return f"▶️ Playing {os.path.basename(file_path)}..."
    except Exception as e:
        return f"Error playing audio: {str(e)}"


def stop_audio():
    global play_obj
    try:
        if play_obj is not None and hasattr(play_obj, "stop"):
            play_obj.stop()
            return "⏹️ Playback stopped."
        else:
            return "Cannot stop playback, unsupported or not started."
    except Exception as e:
        return f"Error stopping playback: {str(e)}"


# theme
sg.theme("DarkGrey13")

# fonts
FONT_TITLE = ("Helvetica", 16, "bold")
FONT_TEXT = ("Helvetica", 12)

# holds all completed operations for the LLM to view
applied_operations = []
latest_bpm = None  # stores last detected BPM

# tracks the last edited file for LLM
previous_file = None


# summary for the LLM based on previous operations (if any)
# this allows the LLM to offer help based on what the user has done
def generate_summary(file_path, bpm=None):
    summary = f"File: {os.path.basename(file_path)}\n\n"
    if applied_operations:
        summary += "Operations applied:\n"
        for op in applied_operations:
            summary += f"• {op}\n"
    else:
        summary += "No audio operations have been applied yet.\n"
    if bpm:
        summary += f"\n Detected BPM: {bpm}"
    return summary


# Layout
layout = [
    [sg.Text("Audio Processing Assistant", font=FONT_TITLE, justification='center', expand_x=True)],
    [sg.HorizontalSeparator()],

    # audio file selection window
    [sg.Text("🎵 Select an audio file:", font=FONT_TEXT),
     sg.Input(key="-FILE-", font=FONT_TEXT, expand_x=True),
     sg.FileBrowse(file_types=(("Audio Files", "*.wav"),), font=FONT_TEXT)],
    [sg.Push(),
     sg.Button("▶️ Play Audio", button_color=("white", "green"), font=FONT_TEXT),
     sg.Button("⏹️ Stop", button_color=("white", "red"), font=FONT_TEXT),
     sg.Push()],

    # Audio tool buttons
    [sg.Frame("🛠 Manual Operations", [
        [sg.Button("Normalize", size=(15, 1), font=FONT_TEXT),
         sg.Button("Equalize", size=(15, 1), font=FONT_TEXT),
         sg.Button("Remove Silence", size=(15, 1), font=FONT_TEXT),
         sg.Button("Detect BPM", size=(15, 1), font=FONT_TEXT)],
        [sg.Button("Bass Boost", size=(15, 1), font=FONT_TEXT),
         sg.Button("Reverb", size=(15, 1), font=FONT_TEXT)],
        [sg.Button("Reverse Audio", size=(15, 1), font=FONT_TEXT)],
        [sg.Button("*New* Suggest Feature", button_color=('white', 'blue'), font=FONT_TEXT)]
    ], expand_x=True)],

    # AI assistant window
    [sg.Frame("🤖 AI Assistant", [
        [sg.Button("Analyze with AI Assistant", button_color=('white', 'green'), font=FONT_TEXT, key="AI Assistant")],
        [sg.Button("*New* Generate Audio Code", button_color=('white', 'green'), font=FONT_TEXT)]
    ], expand_x=True)],

    # output log window
    [sg.Text("📝 Output Log", font=FONT_TEXT)],
    [sg.Multiline(size=(90, 20), key="-OUTPUT-", autoscroll=True, disabled=True, font=("Courier New", 12))],
    [sg.Text("🔊 Live Volume Meter", font=FONT_TEXT)],
    [sg.ProgressBar(max_value=40, orientation='h', size=(40, 20), key='-METER-')],

    [sg.Push(), sg.Button("Exit", font=FONT_TEXT, button_color=("white", "red"))]
]


# launches a separate EQ window for the user when "equalize" is selected.
# this allows the user to make custom EQ moves.
# there are four EQ bands for the user to utilize at preset frequencies.
def show_eq_popup():
    layout = [
        [sg.Text("Adjust Equalizer Gains (in dB)")],
        [sg.Text("60 Hz", size=(8, 1)),
         sg.Slider(range=(-12, 12), resolution=1, orientation='h', size=(30, 15), key="-EQ60-")],
        [sg.Text("250 Hz", size=(8, 1)),
         sg.Slider(range=(-12, 12), resolution=1, orientation='h', size=(30, 15), key="-EQ250-")],
        [sg.Text("1 kHz", size=(8, 1)),
         sg.Slider(range=(-12, 12), resolution=1, orientation='h', size=(30, 15), key="-EQ1K-")],
        [sg.Text("4 kHz", size=(8, 1)),
         sg.Slider(range=(-12, 12), resolution=1, orientation='h', size=(30, 15), key="-EQ4K-")],
        [sg.Button("Apply EQ", button_color=('white', 'green')),
         sg.Button("Cancel", button_color=('white', 'firebrick'))]
    ]

    eq_window = sg.Window("Adjust Equalizer", layout, modal=True)

    while True:
        event, values = eq_window.read()
        if event in (sg.WINDOW_CLOSED, "Cancel"):
            eq_window.close()
            return None  # User clicked cancel
        elif event == "Apply EQ":  # apply EQ moves set by user
            eq_window.close()
            return [
                {'frequency': 60, 'gain': values["-EQ60-"]},
                {'frequency': 250, 'gain': values["-EQ250-"]},
                {'frequency': 1000, 'gain': values["-EQ1K-"]},
                {'frequency': 4000, 'gain': values["-EQ4K-"]},
            ]


# window
window = sg.Window("Audio Processing Assistant", layout, finalize=True, resizable=True)

# welcome message for the user
sg.popup_ok(
    "🎧 Welcome to Audio Processing Assistant!",
    "This application allows you to:",
    "• Select and analyze .wav files",
    "• Apply audio operations: Normalize, Equalize, Remove Silence, Detect BPM",
    "• Enhance your audio with Bass Boost and Reverb",
    "• Get professional feedback from an AI Audio Engineer",
    "• Automatically save all processed files to the 'processed audio' folder",
    title="Welcome",
    keep_on_top=True
)

# event Loop for all audio operations
while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, "Exit"):
        break

    file_path = values["-FILE-"]

    # clears AI history when a new file is selected
    if file_path != previous_file and os.path.isfile(file_path):
        applied_operations.clear()
        latest_bpm = None
        window["-OUTPUT-"].update(f"Selected file: {os.path.basename(file_path)}\n")
        previous_file = file_path

    if event == "*New* Suggest Feature":
        open_feedback_window()


    def open_code_generator():
        layout = [
            [sg.Text("Describe the audio-related Python code you'd like to generate:")],
            [sg.Multiline(size=(60, 10), key="-DESC-")],
            [sg.Button("Generate with AI", button_color=("white", "green")),
             sg.Button("Cancel", button_color=("white", "firebrick"))]
        ]

        window = sg.Window("🧠 Generate Audio Code", layout, modal=True)

        while True:
            event, values = window.read()
            if event in (sg.WINDOW_CLOSED, "Cancel"):
                break
            elif event == "Generate with AI":
                description = values["-DESC-"].strip()
                if not description:
                    sg.popup_error("Please enter a description.")
                    continue

                base_prompt = (
                    "You are a professional developer of various audio systems. "
                    "Create a working Python program based on the description below.\n\n"
                    f"Description: {description}"
                )

                sg.popup_quick_message("Generating code with Gemini...", auto_close_duration=2)
                result = query_llm(base_prompt)
                sg.popup_scrolled(result, title="AI-Generated Code", size=(100, 30), font=("Courier New", 10))
                break

        window.close()


    if event == "*New* Generate Audio Code":
        open_code_generator()

    elif event == "▶️ Play Audio":
        if not os.path.isfile(file_path):
            window["-OUTPUT-"].update("Please select a valid .wav file.\n", append=True)
            continue
        window["-OUTPUT-"].update(f"▶️ Playing {os.path.basename(file_path)}...\n", append=True)
        play_with_meter(file_path, window)

    elif event == "⏹️ Stop":
        result = stop_audio()
        window["-OUTPUT-"].update(result + "\n", append=True)

    elif event == "-METER-UPDATE-":
        window["-METER-"].update_bar(values[event])

    elif event == "-OUTPUT-APPEND-":
        window["-OUTPUT-"].update(values[event], append=True)

    if event in ("Normalize", "Equalize", "Remove Silence", "Detect BPM", "Bass Boost", "Reverb", "Reverse Audio"):
        if not os.path.isfile(file_path):
            window["-OUTPUT-"].update("Please select a valid audio file.\n", append=True)
            continue
        window["-OUTPUT-"].update(f"Performing {event.lower()} on {file_path}...\n", append=True)

        # all if statements follow this structure:
        # perform specified audio tool when button is clicked
        # output file to processed audio folder
        # record operation for the LLM
        if event == "Detect BPM":
            bpm_result = detect_bpm(file_path)
            window["-OUTPUT-"].update(f"{bpm_result}\n", append=True)
            bpm_result = detect_bpm(file_path)
            latest_bpm = bpm_result.split(": ")[-1]  # store the bpm number for LLM
            applied_operations.append(f"Detected BPM: {latest_bpm}")

        elif event == "Normalize":
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_normalized.wav"
            output_path = os.path.join("processed audio", output_filename)
            result = normalize_audio(file_path, output_path)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Normalized audio")

        elif event == "Remove Silence":
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_nosilence.wav"
            output_path = os.path.join("processed audio", output_filename)
            result = remove_silence(file_path, output_path)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Removed silence")

        elif event == "Equalize":
            bands = show_eq_popup()
            if bands is None:
                window["-OUTPUT-"].update("Equalizer canceled by user.\n", append=True)
                continue
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_Equalized.wav"
            output_path = os.path.join("processed audio", output_filename)
            result = apply_equalizer(file_path, output_path, bands)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Applied equalizer (users settings)")

        elif event == "Bass Boost":
            if not os.path.isfile(file_path):
                window["-OUTPUT-"].update("Please select a valid audio file.\n", append=True)
                continue
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_bass.wav"
            output_path = os.path.join("processed audio", output_filename)
            result = bass_boost(file_path, output_path)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Boosted bass frequencies")

        elif event == "Reverb":
            if not os.path.isfile(file_path):
                window["-OUTPUT-"].update("Please select a valid audio file.\n", append=True)
                continue
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_reverb.wav"
            output_path = os.path.join("processed audio", output_filename)

            result = apply_reverb(file_path, output_path)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Added reverb effect")

        elif event == "Reverse Audio":
            os.makedirs("processed audio", exist_ok=True)
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_reversed.wav"
            output_path = os.path.join("processed audio", output_filename)
            result = reverse_audio(file_path, output_path)
            window["-OUTPUT-"].update(result + "\n", append=True)
            applied_operations.append("Reversed audio")

    # if the user selects AI assistant, request response from LLM
    # the LLM will help the user create a professional audio file.
    elif event == "AI Assistant":
        if not os.path.isfile(file_path):
            window["-OUTPUT-"].update("Please select a valid audio file.\n", append=True)
            continue

        # uses previous operations (if any) to give user accurate feedback.
        summary = generate_summary(file_path, bpm=latest_bpm)

        prompt = (
            "You are a professional audio engineer. "
            "Analyze the following audio summary and provide feedback on any remaining issues, and suggest improvements"
            "that could help make the audio sound more professional:\n\n"
            f"{summary}"
        )

        window["-OUTPUT-"].update("\n\n NEW AI RESPONSE \n\n Sending audio summary to AI assistant...\n", append=True)
        ai_response = query_llm(prompt)
        window["-OUTPUT-"].update(ai_response + "\n", append=True)

window.close()
