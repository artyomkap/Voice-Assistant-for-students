Important installation guide:
When submitting work, Dropbox only accepts 2gb.
The model in the voice assistant used for speech recognition takes up 2GB, so it needs to be installed separately on the website (vosk-model-en-us-0.22): https://alphacephei.com/vosk/models
This model must be inserted into the “vosk_model” folder in the project directory.

To install all the necessary libraries, the file regulations.txt was created, which includes a list of all libraries. To install them you need to run the command in the console and in the project path: “pip install requirements.txt”
For all functions to work correctly, you need to specify the paths to all the necessary applications installed on the computer in the config.py file. The student account information and all paths to the required applications must be indicated.
