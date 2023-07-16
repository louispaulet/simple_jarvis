import requests
import speech_recognition as sr
import argparse
import json
import os
import sys

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


def chat_with_gpt(prompt, api_key, model='gpt-3.5-turbo', max_tokens=50, retries=3):
    if not prompt:
        print('Nothing to request, prompt is empty')
        return None

    api_endpoint = 'https://api.openai.com/v1/chat/completions'

    # Create the payload for the API request
    data = {
        'model': model,
        'messages': [{'role': 'system', 'content': 'You are a helpful assistant.'},
                     {'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens
    }

    # Set the headers including your API key
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    for _ in range(retries):
        try:
            # Send the request to the OpenAI API
            response = requests.post(api_endpoint, json=data, headers=headers)
            # Handle the response
            if response.status_code == 200:
                # Get the generated message from the API response
                messages = response.json()['choices'][0]['message']['content']
                return messages
            else:
                print(f'Request failed with status code {response.status_code}')
                continue
        except Exception as e:
            print(f"Failed to request chat completion: {e}")
            continue

    print(f"Failed to get chat completion after {retries} attempts")
    return None


def main(api_key_file, model, max_tokens):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        api_key = load_api_key(api_key_file)
        messages = chat_with_gpt(get_voice_command(r, source), api_key, model, max_tokens)
        print(messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Voice-based chatbot with OpenAI')
    parser.add_argument('--api-key-file', type=str, default='key.txt', help='Path to file containing OpenAI API key')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Model to use for OpenAI Chat API')
    parser.add_argument('--max-tokens', type=int, default=50, help='Maximum number of tokens for Chat API response')
    args = parser.parse_args()

    main(args.api_key_file, args.model, args.max_tokens)
