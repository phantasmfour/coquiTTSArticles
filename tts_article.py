# 08/14/2023

import os
import gc # Trying to help increase memory garbage collection
import re # Cleaning html
import time # for sleeping
import wave  # Used to concatenate audio
import pygame  # Previously used to just test playing the wav's. Can be removed not really needed just remove the function play_wav_file
import requests  # Data from Web
import concurrent.futures  # Wanted to thread to speed up the TTS process. Originally using Coqui so it took a while


from bs4 import BeautifulSoup  # Parsing html
from googletrans import Translator  # Free google translate API, but the catch is hard to get working. Found this version to work googletrans==3.1.0a0
from pydub import AudioSegment # Convert wav to mp3 just using ffmpeg
from datetime import datetime  # Get date and time for filename
from TTS.api import TTS  # Coqui for the voices

# Capture the start time
start_time = time.time()

file_path = "/home/path/you/use/TTS/"  # Where you are going to save things

def play_wav_file(filename):
    '''
    Used in dev when just testing what vocoders should like.
    '''
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

def testtts():
    '''
    Again just using to test the tts voices with the above function. Might be useful later if you need to change.
    '''
    #tts = TTS("tts_models/spa/fairseq/vits")
    #tts.tts_to_file(text="Yo vivo en Granada, una ciudad pequeña que tiene monumentos muy importantes como la Alhambra. Aquí la comida es deliciosa y son famosos el gazpacho, el rebujito y el salmorejo.", file_path="output.wav")
    #play_wav_file("output.wav")
    #os.remove("output.wav")
    tts = TTS("tts_models/eng/fairseq/vits") # solid but not crazy good. the spanish one is best.
    tts.tts_to_file(text="Be careful what you wish for! One man finds this out the hard way when he brings a magical monkey’s paw home from India. This paw is supposed to grant three wishes to three people. People start to wish on it, only to realize that our wishes can have severe consequences.", file_path="output.wav")
    play_wav_file("output.wav")
    os.remove("output.wav")

def translate_text(text, target_language='es'):
    '''
    Translate the english transcripts to spanish for the actual learning. Can change your language here if you wante a different one
    '''
    # Create a Translator object
    translator = Translator()
    # Detect the source language (optional, but can be useful if you're unsure about the input language)
    #detected_lang = translator.detect(text).lang  # not using
    # Translate the text to the target language
    translated_text = translator.translate(text, src="en", dest=target_language)
    return translated_text.text

def tts(arrayOfLines):
    '''
    Using Coqui to load in voices and the synthesize speech. Its not setup to run well on raspberry pi's which runs my code. But piper had some pronunciation issues in spanish I could not fix.
    '''
    # Init TTS via coqui library
    tts_eng = TTS("tts_models/en/vctk/vits")  # You don't need the full path to models here even with cron.
    tts_spa = TTS("tts_models/spa/fairseq/vits")
    
    # Select a specific speaker index for English TTS. This one I liked best. The spanish model only has a single speaker
    eng_speaker_index = 4

    def tts_eng_thread(line, i): # I did not know this was even legal in python but functions within functions giving them the ability to be threaded with calls as single core is slow
        tts_eng.tts_to_file(text=line, file_path=f"{file_path}output_eng_{i}.wav", speaker=tts_eng.speakers[eng_speaker_index])
        gc.collect()  # Memory issues are bad. Feel like its in the coqui library or the threads are holding onto memory for too long. I am not returning anything so maybe they are just kept open. Either way I solved this just by increasing swap

    def tts_spa_thread(line, i):
        translated_text = translate_text(line)
        tts_spa.tts_to_file(text=translated_text, file_path=f"{file_path}output_spa_{i}.wav")
        gc.collect()

    threads = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for i, line in enumerate(arrayOfLines):
            eng_thread = executor.submit(tts_eng_thread, line, i)
            spa_thread = executor.submit(tts_spa_thread, line, i)
            threads.append(eng_thread)
            threads.append(spa_thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.result()

def pullArticle():
    '''
    Pulling and parsing todays article from 1440. 
    Parses it using BS4 and then returns the text. 
    Would be good to filter the ads but not doing as of now since its helpful for the language learning.
    '''
    try:
        response = requests.get("https://join1440.com/today")
        response.raise_for_status()  # Check if the request was successful
        response = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

    if response is not None:
        # Parse the webpage content using BeautifulSoup
        soup = BeautifulSoup(response, 'html.parser')
        lines = []
        # Filtering out some lines that are in every article and not needed.
        filterOutText = [" PREVIOUS NEXT All your news. None of the bias. Become a reader of the daily news briefing known for unbiased content. Join Free Join over 2 million daily readers. 100% free. Unsubscribe anytime. Join over 2.7M people as a reader of the daily news briefing known for unbiased content, summed up in a 5-minute read. Join Free About Today's Briefing Contact Us Partner With Us © 1440 Media, LLC - 2023 Terms & Conditions • Privacy • Cookies This site is protected by reCAPTCHA and the Google Privacy Policy and Terms of Service apply."," Copyright © 2023, 1440 Media, All rights reserved. "," 1440 Media 222 W Merchandise Mart Plaza, Suite 1212 Chicago, IL 60654 "," Interested in reaching smart readers like you? To become a 1440 partner, apply here . "," Send us your feedback at  hello@join1440.com and help us stay unbiased as humanly possible. We’re ready to listen. "," In partnership with "," You share. We listen. As always, send us feedback at hello@join1440.com . "]
        bigText = soup.get_text(separator=' ').split("\n")  # Get text worked the best for this page and splitting on new lines
        for line in bigText:
            if line != " " and line not in lines and not line.isspace():
                line = re.sub(r'[\xa0\n\t\r]', ' ', line)  # some reason there were tehse characters so replacing them with nowthing.
                line = line.replace("  ", " ")  # Double spaces created wierd pausing in transcripts.
                line = line.replace("\\", "")
                if line not in filterOutText:  # Filter
                    lines.append(line)
    return lines


def playArticleLines(articleLines):
    ''' 
    Used to just Dev playing the recordings and then removing them. I was previously using a sleep to slow down the audio before recording a half second blank audio
    I think piper actually will let you pause a certain time after sentences but I was using Coqui at first so I like this method.
    ''' 
    for i in range(len(articleLines)):
        play_wav_file(f"output_eng_{i}.wav")
        os.remove(f"output_eng_{i}.wav")
        time.sleep(1)
        play_wav_file(f"output_spa_{i}.wav")
        os.remove(f"output_spa_{i}.wav")
        time.sleep(1)


def concatenate_wav_files(output_format="wav", frame_rate=22050):
    ''' 
    For each line I feed the TTS model it outputs the text. This was I can have one line english and the next in another language. 
    In doing this we make multiple files for around each line/break in the story.
    I think take these all and combine them and add in a half second wav file with nothing being said to make it sound better.
    ''' 

    output_audio = AudioSegment.empty()
    output_file = f"{file_path}longrunning.mp3"

    wav_files = []
    for i in range(len(articleLines)):
        wav_files.append(f"{file_path}output_eng_{i}.wav")  # English First
        wav_files.append(f"{file_path}half_second_delay.wav")  # half second delay recorded via audacity and no mic
        wav_files.append(f"{file_path}output_spa_{i}.wav")  # Spanish second
        wav_files.append(f"{file_path}half_second_delay.wav")  # half second delay

    for file in wav_files:
        audio = AudioSegment.from_file(file)
        # Resample audio to a common frame rate
        audio = audio.set_frame_rate(frame_rate)
        output_audio += audio

    # Export the concatenated audio to the desired output file format
    output_audio.export(output_file, format="mp3",bitrate="192k",parameters=["-ac", "2", "-vol", "150"])  # Somehow 192 is better sounding than 320k and I lowered this more as discord only lets you put 25mb files. might be good to split it into two for higher bitrates
    # This is a bit hacky and defintely more dynamic ways to do it
    # GPT helped with this. To explain discord limits files over 25mbs being uploaded and I am trying to host them there since its easy.
    # The files are usualy 30-40Mb and not over 50Mb so check if its over 25Mb and just split it in two. Yes if its over 50mb we will have problems. Would be better to host on a vps somewhere so file sizes dont matter
    if os.path.getsize(output_file)/(1024*1024) > 25: 
        # Calculate the duration of each half
        half_duration = len(output_audio) // 2

        # Split the combined audio into two equal halves
        first_half = output_audio[:half_duration]
        second_half = output_audio[half_duration:]

        # Export the two halves as separate MP3 files
        output_first_half = f"{output_file[:-4]}_part1.mp3"
        output_second_half = f"{output_file[:-4]}_part2.mp3"
        first_half.export(output_first_half, format="mp3", bitrate="192k")
        second_half.export(output_second_half, format="mp3", bitrate="192k")
        os.remove(output_file)
    [os.remove(x) for x in wav_files if x != f"{file_path}half_second_delay.wav"]  # One liner to delete all the wav_files we combined but not the half second delay one.

def upload_new_file():
    ''' 
    You can store these files anywhere. Discord webhooks are super easy but the 25mb hurts but is understandable.
    There is better ways to do this but this is the quickest I came up with for a simple project
    '''
    webhook_url = "https://discord.com/api/webhooks/your_webhook_url_here"
    
    if os.path.exists(f"{file_path}longrunning.mp3"):  # Again hacky but if there is one file just upload it.
        with open(f"{file_path}longrunning.mp3", "rb") as file:
            file_content = file.read()
        files = {
            "file": (f"{datetime.now().date()}-1440.mp3", file_content)
        }
        response = requests.post(webhook_url, files=files)
        #print(response.status_code)
        os.remove(f"{file_path}longrunning.mp3")
    else:  # If not the file was over 25mbs so upload both parts.
        #print("too big")
        with open(f"{file_path}longrunning_part1.mp3", "rb") as file:
            file_content_1 = file.read()
        with open(f"{file_path}longrunning_part2.mp3", "rb") as file:
            file_content_2 = file.read()
        files = {
            "file": (f"{datetime.now().date()}-1440_p1.mp3", file_content_1)
        }
        response = requests.post(webhook_url, files=files)
        #print(response.status_code)
        os.remove(f"{file_path}longrunning_part1.mp3")
        file2 = {
            "file": (f"{datetime.now().date()}-1440_p2.mp3", file_content_2)
        }
        response = requests.post(webhook_url, files=file2)
        #print(response.status_code)
        os.remove(f"{file_path}longrunning_part2.mp3")
        # You sadly cannot send two 25mb files in the same request either.
        # Again I am not handling any errors to reupload. But discord usually does not reject them.

articleLines = pullArticle()
tts(articleLines)
concatenate_wav_files(articleLines)
upload_new_file()

end_time = time.time()
runtime = end_time - start_time
print(f"Script runtime: {runtime:.4f} seconds")

'''
Links:
https://github.com/rhasspy/piper
https://tts.readthedocs.io/en/dev/tutorial_for_nervous_beginners.html
https://github.com/coqui-ai/TTS/discussions/1891
https://github.com/topics/voice-cloning
https://github.com/jiaaro/pydub
'''
