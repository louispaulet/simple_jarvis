import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import re
import sys
import time
import tempfile
import argparse
import requests
import speech_recognition as sr
import pygame
import json
import openai
import multiprocessing
import pygame.mixer
import pydub
from gtts import gTTS
from langdetect import detect


class ChatBot:
    def __init__(self, api_key_file, model='gpt-3.5-turbo', max_tokens=500):
        self.api_key = self.load_api_key(api_key_file)
        self.model = model
        self.max_tokens = max_tokens
        self.recognizer = sr.Recognizer()

    def load_api_key(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Failed to load API key: {e}")
            sys.exit(1)

    def get_voice_command(self, source, retries=3):
        for _ in range(retries):
            print("Speak now:")
            audio = self.recognizer.listen(source)
            try:
                command = self.recognizer.recognize_google(audio, language='fr-FR')
                print(f"Command received: {command}")
                if command.strip() == '':
                    print("The command is empty")
                    continue
                return command
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand your command")
            except sr.RequestError as e:
                print(f"An error occurred when making a request to the Google Speech Recognition API: {e}")
        print(f"Failed to get voice command after {retries} attempts")
        return None

    def communicate_with_gpt(self, prompt, shared_queue, shared_stop_signal):
        if not prompt:
            print('Nothing to request, prompt is empty')
            shared_stop_signal.put(True)
            return None

        openai.api_key = self.api_key
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}],
            temperature=0,
            max_tokens=self.max_tokens,
            stream=True
        )
        self.process_and_store_responses(response, shared_queue, shared_stop_signal)

    def process_and_store_responses(self, response, shared_queue, shared_stop_signal):
        curr_sentence = []
        for chunk in response:
            chunk_text = self.extract_text_from_chunk(chunk)
            if chunk_text is not None:
                curr_sentence.append(chunk_text)
                complete_sentence = ''.join(curr_sentence)

                if self.contains_sentence_delimiters(chunk_text):
                    shared_queue.put(complete_sentence)
                    curr_sentence = []
                elif self.contains_intermediate_delimiters(complete_sentence):
                    split_sentences = self.split_at_intermediate_delimiter(complete_sentence)
                    shared_queue.put(split_sentences[0])
                    curr_sentence = [split_sentences[1]]

        if len(curr_sentence):
            shared_queue.put(''.join(curr_sentence))

        shared_stop_signal.put(True)

    @staticmethod
    def extract_text_from_chunk(chunk):
        try:
            chunk_content = chunk['choices'][0]['delta']['content']
            return chunk_content if isinstance(chunk_content, str) else None
        except KeyError:
            return None

    @staticmethod
    def contains_sentence_delimiters(chunk_text):
        return '\n' in chunk_text or ':' in chunk_text or ';' in chunk_text

    @staticmethod
    def contains_intermediate_delimiters(complete_sentence):
        return re.search(r'\,\s', complete_sentence) or re.search(r'\.\s', complete_sentence)

    @staticmethod
    def split_at_intermediate_delimiter(complete_sentence):
        return re.split(r'\,\s|\.\s', complete_sentence, 1)

    @staticmethod
    def speak(text, complete_text):
        print(text)
        detected_language = detect(complete_text)

        tts = gTTS(text=text, lang=detected_language)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            tts.save(temp_filename)
            temp_file.close()

        sound = pydub.AudioSegment.from_file(temp_filename)
        sound = sound.speedup(playback_speed=1.3)

        modified_temp_filename = temp_filename + "_modified.wav"
        sound.export(modified_temp_filename, format="wav")

        pygame.mixer.init()

        modified_sound = pygame.mixer.Sound(modified_temp_filename)

        modified_sound.play()

        while pygame.mixer.get_busy():
            continue

        sound_duration = modified_sound.get_length()
        modified_sound.stop()

        os.remove(temp_filename)
        os.remove(modified_temp_filename)

        return sound_duration

    def speak_responses(self, shared_queue, shared_complete_text, shared_stop_signal):
        complete_text = ''

        while True:
            if not shared_queue.empty():
                response = shared_queue.get()
                complete_text += response

                if len(response) > 1:
                    self.speak(response, complete_text)

            if shared_queue.empty() and not shared_stop_signal.empty():
                break

        shared_complete_text.put(complete_text)


def main(api_key_file):
    chatbot = ChatBot(api_key_file)

    with sr.Microphone() as source:
        voice_command = chatbot.get_voice_command(source)

    shared_queue = multiprocessing.Queue()
    shared_stop_signal = multiprocessing.Queue()
    shared_complete_text = multiprocessing.Queue()

    communicate_process = multiprocessing.Process(target=chatbot.communicate_with_gpt, args=(voice_command, shared_queue, shared_stop_signal))
    speak_process = multiprocessing.Process(target=chatbot.speak_responses, args=(shared_queue, shared_complete_text, shared_stop_signal))

    communicate_process.start()
    speak_process.start()

    communicate_process.join()
    speak_process.join()

    complete_text = shared_complete_text.get()
    print(f"Complete text: {complete_text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Communicate with the GPT-3 model using voice commands.')
    parser.add_argument('--api_key_file', default='key.txt', type=str, required=False, help='Path to the file containing the OpenAI API key.')
    args = parser.parse_args()

    main(args.api_key_file)

