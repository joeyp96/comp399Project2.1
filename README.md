* to run the program *

- Add all files in this repository to a new pycharm project. (python 3.11 reccomended)
- raw audio files may stay in the raw audio files folder within the currect working directory for testing. 

- you must install these packages:
- 
- pip install PySimpleGUI
- pip install numpy
- pip install scipy
- pip install soundfile
- pip install librosa
-
- you must create a secret.txt file in the current working directory.
- paste your hugging face API key there with no spaces or variable names, just the key.
- I did this for security as git hub uses projects to train AI models.

- python 3.11 using pycharm is highly reccomended as that was the interpreter version used to create the program.

* what the program does *

- This program is an audio processing application that incorporates an AI model.
- The user may select an audio file and then chose from a list of multiple audio operations to perform on the file.
- At any point, the user may click the AI assistant button to get feedback on the audio operations performed (if any) or
- what to do next. The user must have an audio file selected to do anything.
- Once an audio operation has completed, the file will export to a folder called processed audio.
- this folder will be created automatically after your first operation completes.

* important *
- I attempted to include an audio file to allow anyone to test the remove silence function, but the file was too large.
- If there is no silence detected, the process will fail.
- If there is silence, you will get warnings but the process will work.
- this is due to FFMPEG not being supported.
- If you must see this process work, I may demo it for you in class.
- Otherwise, you may find a .wav file that has a long silence at the end and try it. (try 30sec of silence or so)

- 
