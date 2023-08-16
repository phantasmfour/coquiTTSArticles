# Helping me learn a new language while creating audio articles

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





