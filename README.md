# Helping me learn a new language while creating AI Synthesized Recordings

In this project I had the idea to take the articles I read in the morning and convert them into an audiobook that is read in two languages.
What tts_article.py does
- Scrape a website for text of a daily article.
- Using Coqui TTS it will translate the text to speech in an audio file
- We convert the text into spanish using the Google Translate API
- Coqui creates audio files in the second langauge
- Take each paragraph of english audio and put the spanish translation after.
- Concatanate all the audio into a single audio file
- Upload that audio file to discord for easy listening

This project can be very easily modified to change the text you provide to Coqui and the place where you are storing these audio files.
You could even start converting books you own into audio books.

This is setup and running on a raspberry pi. It is very slow and needs a lot of ram. I originally tried using the piper library but found its outputs to have issues pronouncing R's.
I included the conda env file along with a requirments.txt and two sample output files.

More info here: https://phantasmfour.com/learning-a-language-with-voice-synthesis/



