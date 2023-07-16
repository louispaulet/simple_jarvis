import requests
import speech_recognition as sr
import argparse
import json
import os
import sys
from gtts import gTTS
from langdetect import detect
from tempfile import TemporaryFile
import pygame
import openai

def get_voice_command(r, source, retries=3):
    for _ in range(retries):
        print("Parlez maintenant :")
        audio = r.listen(source)
        try:
            command = r.recognize_google(audio, language='fr-FR')
            print(f"Commande reçue : {command}")
            if command.strip() == '':
                print("La commande est vide")
                continue
            return command
        except sr.UnknownValueError:
            print("Google Speech Recognition n'a pas compris ce que vous avez dit")
        except sr.RequestError as e:
            print(f"Une erreur s'est produite lors de la requête à l'API Google Speech Recognition ; {e}")

    print(f"Failed to get voice command after {retries} attempts")
    return None


def load_api_key(file_path):
    try:
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
        return api_key
    except Exception as e:
        print(f"Failed to load API key: {e}")
        sys.exit(1)

def get_chunk_text(text_chunk):
  if text_chunk is None:
    return None

  try:
    if text_chunk['choices'][0]['delta']['content'] is not None:
      chunk_text = text_chunk['choices'][0]['delta']['content']
      if isinstance(chunk_text, str):
        return chunk_text
      else:
        return None

  except KeyError as e:
    return None


def chat_with_gpt(prompt, api_key, model='gpt-3.5-turbo', max_tokens=500, retries=1):
    if not prompt:
        print('Nothing to request, prompt is empty')
        return None
    
    
    openai.api_key = api_key
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                     {'role': 'user', 'content': prompt}],
        temperature=0,
        max_tokens = max_tokens,
        stream=True  # this time, we set stream=True
    )
    
    curr_sentence = []
    for chunk in response:
        chunk_text = get_chunk_text(chunk)
        if chunk_text is not None:
            curr_sentence.append(chunk_text)

            if '\n' in chunk_text:
              complete_sentence = ''.join(curr_sentence)
              curr_sentence = []
              print(complete_sentence)
              # problem here! - the .mp3 is being read while the next tries to be written!
              #speak(complete_sentence)
    return None

def speak(text):
    detected_language = detect(text)
    tts = gTTS(text=text, lang=detected_language)
    tts.save('temp.mp3')

    pygame.mixer.init()
    pygame.mixer.music.load('temp.mp3')
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        continue

    pygame.mixer.music.stop()

def main(api_key_file, model, max_tokens):
    api_key = load_api_key(api_key_file)
    messages = chat_with_gpt("donne moi la recette de la tarte aux pommes", api_key, model, max_tokens)
    return None
    r = sr.Recognizer()
    with sr.Microphone() as source:
        api_key = load_api_key(api_key_file)
        messages = chat_with_gpt(get_voice_command(r, source), api_key, model, max_tokens)
        print(messages)
        speak(messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Voice-based chatbot with OpenAI')
    parser.add_argument('--api-key-file', type=str, default='key.txt', help='Path to file containing OpenAI API key')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Model to use for OpenAI Chat API')
    parser.add_argument('--max-tokens', type=int, default=500, help='Maximum number of tokens for Chat API response')
    args = parser.parse_args()

    main(args.api_key_file, args.model, args.max_tokens)
