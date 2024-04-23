import json
import logging
import struct
import time
import webbrowser
import yaml
import pyttsx3
import requests
import pvporcupine, pyaudio
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
import simpleaudio as sa
import os, random
from pycaw.api.endpointvolume import IAudioEndpointVolume
from vosk import Model, KaldiRecognizer
from commands import check_email, weather, exam_timetable, ntu_timetable, ntu_news_and_events, word_document
import config
import tts
import subprocess
import faulthandler
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

faulthandler.enable()

print('Initializing VOSK model...')
vosk = Model('vosk_model/vosk-model-en-us-0.22')
kaldi_rec = KaldiRecognizer(vosk, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
logging.basicConfig(filename='app.log', level=logging.DEBUG)

porcupine = pvporcupine.create(
    access_key=config.PICOVOICE_TOKEN,
    keyword_paths=['./activate_commands/Hello-Summer_en_windows_v3_0_0.ppn',
                   './activate_commands/Hey-Summer_en_windows_v3_0_0.ppn']
)

CDIR = os.getcwd()
VA_CMD_LIST = yaml.safe_load(
    open('commands/commands_file.yaml', 'rt', encoding='utf8'),
)


def change_volume(volume_change_percent):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    current_volume = volume.GetMasterVolumeLevelScalar()
    new_volume = max(0.0, min(1.0, current_volume + volume_change_percent))
    volume.SetMasterVolumeLevelScalar(new_volume, None)


def get_query():
    start_time = time.time()
    while time.time() - start_time < 10:
        pcm = recorder.read()
        sp = struct.pack("h" * len(pcm), *pcm)
        if kaldi_rec.AcceptWaveform(sp):
            text = json.loads(kaldi_rec.Result())["text"].lower()
            print(f'Recognized: {text}')
            return text


def search_in_browser(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)


def read_emails():
    emails = check_email.get_first_5_emails()
    for email in emails:
        tts.va_speak(f'Email from: {email.SenderEmailAddress}, Subject: {email.Subject}')


def open_outlook():
    subprocess.Popen(config.OUTLOOK_PATH)
    play('okay')


def listen_for_yes_no():
    start_time = time.time()
    while time.time() - start_time < 10:
        pcm = recorder.read()
        sp = struct.pack("h" * len(pcm), *pcm)
        if kaldi_rec.AcceptWaveform(sp):
            text = json.loads(kaldi_rec.Result())["text"].lower()
            print(f'Recognized: {text}')
            if "yes" in text:
                return 'yes'
            elif "yes please" in text:
                return 'yes'
            elif "sure" in text:
                return 'yes'
            elif "of course" in text:
                return 'yes'
            elif "yeah" in text:
                return 'yes'
            elif "okay" in text:
                return 'yes'
            elif "no" in text:
                play('okay')
                break
            elif text is None:
                break
            else:
                play('i dont know')
                break


def va_respond(voice: str):
    global recorder, message_log, fisrt_request
    print(f'Recognized: {voice}')
    cmd = recognize_cmd(filter_cmd(voice))
    print(cmd)

    if len(cmd['cmd'].strip()) <= 0:
        return False
    elif cmd['percent'] < 70 or cmd['cmd'] not in VA_CMD_LIST.keys():
        # play('not found')
        if fuzz.ratio(voice.join(voice.split()[:1]).strip(), 'say') > 75:
            message_log.append({"role": 'user', "content": voice})
            message_log.append({"role": 'assistant', "content": 'response'})

            recorder.stop()
            # tts speak
            time.sleep(0.5)
            recorder.start()
            return False
        else:
            play('i dont know')
            time.sleep(1)
        return False
    else:
        execute_cmd(cmd['cmd'], voice)
        return True


def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in VA_CMD_LIST.items():

        for x in v:
            vrt = fuzz.ratio(cmd, x)
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt

    return rc


def filter_cmd(raw_voice: str):
    cmd = raw_voice
    for x in config.VA_ALIAS:
        cmd = cmd.replace(x, "").strip()

    for x in config.VA_TBR:
        cmd = cmd.replace(x, "").strip()
    return cmd


def execute_cmd(cmd: str, voice: str):
    if cmd == 'timetable_this':
        play('okay')
        timetable_list = ntu_timetable.get_timetable_this_week()
        for time_timetable in timetable_list:
            tts.va_speak(time_timetable)
    elif cmd == 'timetable_next':
        play('okay')
        try:
            timetable_list = ntu_timetable.get_timetable_next_week()
            for time_timetable in timetable_list:
                tts.va_speak(time_timetable)
        except Exception as e:
            print(f"An error occurred while fetching timetable: {e}")
    elif cmd == 'thanks':
        play("thanks")
    elif cmd == 'check':
        play('check')
    elif cmd == 'open_browser':
        subprocess.Popen([f'{config.BROWSER_PATH}'])
        play('okay')
    elif cmd == 'open_discord':
        subprocess.Popen([f'{config.DISCORD_PATH}'])
        play('okay')
    elif cmd == 'check_new_emails':
        play('okay')
        output = check_email.check_new_emails_manual()
        if output == 1:
            play('1 email')
            play('would you like to hear')
            decision = listen_for_yes_no()
            if decision == 'yes':
                read_emails()
                play('open outlook')
                decision2 = listen_for_yes_no()
                if decision2 == 'yes':
                    open_outlook()
        if 1 < output <= 5:
            play(f'{str(output)} email')
            play('would you like to hear')
            decision = listen_for_yes_no()
            if decision == 'yes':
                read_emails()
                play('open outlook')
                decision2 = listen_for_yes_no()
                if decision2 == 'yes':
                    open_outlook()
        elif output > 5:
            play('more 5')
            play('would you like to hear')
            decision = listen_for_yes_no()
            if decision == 'yes':
                read_emails()
                play('open outlook')
                decision2 = listen_for_yes_no()
                if decision2 == 'yes':
                    open_outlook()
        else:
            play('0 emails')
            play('open outlook')
            decision2 = listen_for_yes_no()
            if decision2 == 'yes':
                open_outlook()
    elif cmd == 'increase_sound':
        change_volume(0.25)
        play('okay')
    elif cmd == 'decrease_sound':
        change_volume(-0.25)
        play('okay')
    elif cmd == 'mute_sound':
        change_volume(-1.0)
        play('okay')
    elif cmd == 'unmute_sound':
        change_volume(1.0)
        play('okay')
    elif cmd == 'search_browser':
        play('search')
        query = get_query()
        play('okay')
        search_in_browser(query)
    elif cmd == 'open_spotify':
        play('okay')
        subprocess.Popen([f'{config.SPOTIFY_PATH}'])
    elif cmd == 'play_spotify':
        play('okay')
        subprocess.Popen([f'C:\\Users\\Артем\\VoiceAssistantFYP\\custom_commands\\spotfy_play_pause.exe'])
    elif cmd == 'pause_spotify':
        play('okay')
        subprocess.Popen([f'C:\\Users\\Артем\\VoiceAssistantFYP\\custom_commands\\spotfy_play_pause.exe'])
    elif cmd == 'next_song':
        play('okay')
        subprocess.Popen([f'C:\\Users\\Артем\\VoiceAssistantFYP\\custom_commands\\spotify_next_song.exe'])
    elif cmd == 'previous_song':
        play('okay')
        subprocess.Popen([f'C:\\Users\\Артем\\VoiceAssistantFYP\\custom_commands\\spotify_previous_song.exe'])
    elif cmd == 'get_weather':
        play('okay')
        weather_desc, weather_text = weather.get_weather()
        tts.va_speak(f"It is {weather_desc} in Nottingham, and temperature is {weather_text} celsius")
    elif cmd == 'get_exam_timetable':
        play('okay')
        try:
            exam_list = exam_timetable.get_exam_timetable()
            for time_exam in exam_list:
                tts.va_speak(time_exam)
        except Exception as e:
            print(f"An error occurred while fetching timetable: {e}")
    elif cmd == 'get_university_news':
        play('okay')
        list_news = ntu_news_and_events.get_news()
        for new in list_news:
            tts.va_speak(new)
    elif cmd == 'get_university_events':
        play('okay')
        list_events = ntu_news_and_events.get_events()
        for event in list_events:
            tts.va_speak(event)
    elif cmd == 'new_coursework':
        play('okay')
        word_document.create_word_file()
        time.sleep(1)
        subprocess.Popen(['start', '', 'C:\\Users\\Артем\\Desktop\\New Coursework.docx'], shell=True)



def text_to_speech(input):
    if "the" in input:
        input = input.replace("the", "")
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('language', 'en')
    rate = engine.getProperty('rate')  # getting details of current speaking rate
    text = input
    engine.say(text)
    engine.runAndWait()


def play(phrase, wait_done=True):
    global recorder
    filename = f'{CDIR}\\Summer Sounds Pack\\'

    if phrase == "greet":
        filename += f'greets\\greet{random.choice([1, 2, 3, 4])}.wav'
    elif phrase == 'thanks':
        filename += 'gratitudes\\thank.wav'
    elif phrase == 'run':
        filename += f'common\\run{random.choice([1, 2, 3])}.wav'
    elif phrase == 'check':
        filename += f'common\\yes{random.choice([1, 2, 3])}.wav'
    elif phrase == 'okay':
        filename += f'common\\ok{random.choice([1, 2, 3])}.wav'
    elif phrase == '1 email':
        filename += f'emails\\1 email.wav'
    elif phrase == '2 email':
        filename += f'emails\\2 emails.wav'
    elif phrase == '3 email':
        filename += f'emails\\3 emails.wav'
    elif phrase == '4 email':
        filename += f'emails\\4 emails.wav'
    elif phrase == '5 email':
        filename += f'emails\\5 emails.wav'
    elif phrase == '0 emails':
        filename += f'emails\\no new emails.wav'
    elif phrase == 'more 5':
        filename += f'emails\\more than five emails.wav'
    elif phrase == "would you like to hear":
        filename += f'emails\\would you like to hear.wav'
    elif phrase == 'search':
        filename += f'search\\search{random.choice([1, 2, 3])}.wav'
    elif phrase == 'i dont know':
        filename += f'common\\idk{random.choice([1, 2, 3])}.wav'
    elif phrase == 'open outlook':
        filename += f'emails\\open outlook.wav'

    if wait_done:
        recorder.stop()

    mp3_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = mp3_obj.play()

    if wait_done:
        play_obj.wait_done()
        recorder.start()


recorder = PvRecorder(device_index=0, frame_length=porcupine.frame_length)
recorder.start()
print('Using device: %s' % recorder.selected_device)

print(f"Summer started to work")
play("run")
time.sleep(0.5)
try:
    ltc = time.time() - 1000
except Exception as err:
    logging.exception('Error: ', err)
    print(f"Unexpected {err=}, {type(err)=}")
    raise

try:
    while True:
        try:
            start_time = time.time()
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                end_time = time.time()
                print(f"Activation phrase recognized in {end_time - start_time} seconds.")
                recorder.stop()
                play("greet", True)
                print("Yes, sir.")
                recorder.start()  # prevent self-recording
                ltc = time.time()

            while time.time() - ltc <= 10:
                start_time = time.time()
                pcm = recorder.read()
                sp = struct.pack("h" * len(pcm), *pcm)

                if kaldi_rec.AcceptWaveform(sp):
                    if va_respond(json.loads(kaldi_rec.Result())["text"]):
                        end_time = time.time()
                        print(f"Speech recognized in {end_time - start_time} seconds.")
                        ltc = time.time()
                    break

            if time.time() - ltc >= 420:
                output = check_email.check_new_emails_auto()
                if output == 1:
                    play('1 email')
                    play('would you like to hear')
                    decision = listen_for_yes_no()
                    if decision == 'yes':
                        read_emails()
                        play('open outlook')
                        decision2 = listen_for_yes_no()
                        if decision2 == 'yes':
                            open_outlook()
                if 1 < output <= 5:
                    play(f'{str(output)} email')
                    play('would you like to hear')
                    decision = listen_for_yes_no()
                    if decision == 'yes':
                        read_emails()
                        play('open outlook')
                        decision2 = listen_for_yes_no()
                        if decision2 == 'yes':
                            open_outlook()
                elif output > 5:
                    play('more 5')
                    play('would you like to hear')
                    decision = listen_for_yes_no()
                    if decision == 'yes':
                        read_emails()
                        play('open outlook')
                        decision2 = listen_for_yes_no()
                        if decision2 == 'yes':
                            open_outlook()

                ltc = time.time() - 10

        except Exception as err:
            logging.exception('Error: ', err)
            print(f"Unexpected {err=}, {type(err)=}")
            raise
except Exception as err:
    logging.exception('Error: ', err)
    print(f"Unexpected {err=}, {type(err)=}")
    raise
