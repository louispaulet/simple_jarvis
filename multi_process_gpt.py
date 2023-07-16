import re
import tempfile
import time
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
import multiprocessing

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


def chat_with_gpt(prompt, api_key, model='gpt-3.5-turbo', max_tokens=500, shared_queue=''):
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

            complete_sentence = ''.join(curr_sentence)
            #case of a simple delimiter in current chunk
            if (('\n' in chunk_text) or (':' in chunk_text) or (';' in chunk_text)):
              
              curr_sentence = []
              shared_queue.put(complete_sentence)
              
            #case of comma followed by space
            elif (re.search(r'\,\s', complete_sentence)):
              
              shared_queue.put(complete_sentence.split(',')[0])
              curr_sentence = [complete_sentence.split(',')[1]]
              
            
            #case of period followed by space
            elif (re.search(r'\.\s', complete_sentence)):
              
              shared_queue.put(complete_sentence.split('.')[0])
              curr_sentence = [complete_sentence.split('.')[1]]
              
              
    return None

def speak(text, complete_text):
    print('==============================')
    print(text)
    print('==============================')
    detected_language = detect(complete_text)
    #print(complete_text)
    tts = gTTS(text=text, lang=detected_language)

    # Create a temporary file to store the speech output
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_filename = temp_file.name
        tts.save(temp_filename)

    # Close the temporary file before loading it into pygame
    temp_file.close()

    # Play the speech output
    pygame.mixer.init()
    sound = pygame.mixer.Sound(temp_filename)
    sound.play()
    
    # Wait until the speech is finished playing
    while pygame.mixer.get_busy():
        continue

    # Get sound duration and return it
    sound_duration = sound.get_length()

    # Stop the sound
    sound.stop()

    # Delay the deletion of the temporary file until after playback
    os.remove(temp_filename)

    return sound_duration  # return the sound duration

def speak_the_queue(shared_queue, shared_complete_text):
    while True:
        if not shared_queue.empty():
            text = shared_queue.get()
            if not shared_complete_text.empty():
                complete_text = shared_complete_text.get()
            else:
                complete_text = text
            
            #update the complete text with latest sentence
            shared_complete_text.put(complete_text+text)
            
            duration = speak(text, complete_text)

            # Sleep for the duration of the sound
            #time.sleep(duration/100)
            time.sleep(0.01)
        else:
            #print('empty queue, waiting')
            time.sleep(0.01)




def main(api_key_file, model, max_tokens, shared_queue):
    #api_key = load_api_key(api_key_file)
    #messages = chat_with_gpt("donne moi la recette de la tarte aux pommes", api_key, model, max_tokens, shared_queue)
    #return None
    r = sr.Recognizer()
    with sr.Microphone() as source:
        api_key = load_api_key(api_key_file)
        chat_with_gpt(get_voice_command(r, source), api_key, model, max_tokens, shared_queue)
        #print(messages)
        #speak(messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Voice-based chatbot with OpenAI')
    parser.add_argument('--api-key-file', type=str, default='key.txt', help='Path to file containing OpenAI API key')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Model to use for OpenAI Chat API')
    parser.add_argument('--max-tokens', type=int, default=500, help='Maximum number of tokens for Chat API response')
    args = parser.parse_args()
    #print(args)
    
    
    manager = multiprocessing.Manager()
    shared_queue = manager.Queue()
    shared_complete_text = manager.Queue()

    process1 = multiprocessing.Process(target=main, args=(args.api_key_file, args.model, args.max_tokens, shared_queue))
    process2 = multiprocessing.Process(target=speak_the_queue, args=(shared_queue,shared_complete_text))
    
    process1.start()
    process2.start()
    
    process1.join()
    process2.join()

    #main(args.api_key_file, args.model, args.max_tokens)
