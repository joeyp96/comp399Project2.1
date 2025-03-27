 *to run the program*


- Add all files in this repository to a new pycharm project. (python 3.11 reccomended)
- raw audio files may stay in the raw audio files folder within the currect working directory for testing. 

- you must install these packages:
- 
- pip install PySimpleGUI
- pip install numpy
- pip install scipy
- pip install soundfile
- pip install librosa
- pip install huggingface_hub
- 
- you must create a secret.txt file in the current working directory.
- paste your hugging face API key there with no spaces or variable names, just the key.
- I did this for security as git hub uses projects to train AI models.
-
- From here, you should be able to run the program which will launch the GUI.

- python 3.11 using pycharm is highly reccomended as that was the interpreter version used to create the program.

- The main.py file contains all GUI functionality and makes calls to the audio tools.py file to process the audio. 



  *what the program does*



- This program is an audio processing application that incorporates an AI model.
- once the GUI is launched:
- The user must select an audio file and then chose from a list of multiple audio operations to perform on the file.
- At any point, the user may click the AI assistant button to get feedback on the audio operations performed (if any) or
- what to do next. The user must have an audio file selected to do anything.
- Once an audio operation has completed, the file will export to a folder called processed audio.
- this folder will be created automatically after your first operation completes.


  *important*

  
- this program only supports .wav files. 
- I attempted to include an audio file to allow anyone to test the remove silence function, but the file was too large.
- If there is no silence detected, the process will fail.
- If there is silence, you will get warnings but the process will work.
- this is due to FFMPEG not being supported.
- If you must see this process work, I may demo it for you in class.
- Otherwise, you may find a .wav file that has a long silence at the end and try it. (try 30sec of silence or so)


  *conclusion*

  
- This portion of the read me contains what my goals were initially, the issues I encountered, and what I learned.

- I almost achieved exactly what I set out for initially. I wanted an audio processing application where a user could
- manually select audio operations to perform on a file and also pass an audio file to an LLM for review and further processing.
- however, the main issue that I ran into is that the qwen-audio model cannot be accessed through an API key,
- it has to be run locally and my computer is not powerful enough to run the model.
- Additionally, I could not find an alternative option that was free in order to pass an LLM raw audio files.

- This is where what I learned comes into play. I learned that I could store all operations performed on each file (if any)
- and pass that data to the LLM with my prompt. This allows the model to not only function as an audio engineering assistant
- due to the prompt, but give specific feedback based on what the user as already done. (or what they havent done)
- Once I got this working, I was quite happy with the result. It functions has an entry level audio processing application
- and provides high level feedback on how to further improve your audio for implementing it into a real mix.
- All in all I found this project quite challenging but I feel good about what I've accomplished here. I've
- also programmed this application in a way where I can build off of it later as my knowledge and skills grow.
- If we have a project 3 this semester I may take this further if it alligns with the assignment. 
