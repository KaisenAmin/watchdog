# import required libraries
import sounddevice as sd
from scipy.io.wavfile import write
import wavio as wv
import speech_recognition as sr
import os
import psutil
from gtts import gTTS 
from playsound import playsound

def checkIfProcessRunning(processName):
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return [True, proc]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def play_text_sound(my_text):
    myobj = gTTS(text=my_text, lang='en', slow=False) 
    file_address = os.path.dirname(__file__) 

    file_address = self.file_address[::-1]
    file_address = self.file_address[self.file_address.find('\\')+1:]
    file_address = self.file_address[::-1]

    myobj.save(file_address + "\\Voice\\voice_assistant.mp3") 
    playsound(file_address + "\\Voice\\voice_assistant.mp3")

def start_process(address, process_name, operation):
    pass 

def kill_process(operation, process_name):
    process_name += ".exe"
    call_check_process = checkIfProcessRunning(process_name)

    if call_check_process[0] and operation == 'kill':
        # call_check_process[1]().kill(process_name)
        os.system(f'taskkill /IM {process_name} /F')
        text = process_name + ' is killed'
        play_text_sound(text)

    else:
        text = "It is not a process for killing"
        play_text_sound(text)


def calculate_text(text_voice):
    flag_value = None  
    process_name = None 
    flag = False 

    for text in text_voice:
        text = text.lower()
        print(text)
        if text == 'start' or text == 'kill':
            flag_value = text 
        elif text == 'process':
            flag = True 
        elif flag and flag_value == 'kill':
            process_name = text
            kill_process(flag_value, process_name)
        elif flag and flag_value == 'start':
            process_name = text 
            start_process(address_process, process_name, operation)


def speech_rec():
    file_address = os.path.dirname(__file__)
    freq = 44100
    duration = 5

    recording = sd.rec(int(duration * freq),
                    samplerate=freq, channels=2)
    sd.wait()

    wv.write(file_address + "\\Voice\\recording1.wav", recording, freq, sampwidth=2)

    r = sr.Recognizer()
    h = sr.AudioFile(file_address + "\\Voice\\recording1.wav")

    with h as source:
        audio = r.record(source, duration=5)

    text_voice = r.recognize_google(audio)
    text_voice = str(text_voice).split(' ')
    calculate_text(text_voice)








