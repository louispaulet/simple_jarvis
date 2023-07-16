import requests
import speech_recognition as sr

def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Parlez maintenant :")
        audio = r.listen(source)
        try:
            command = r.recognize_google(audio, language='fr-FR')
            print(f"Commande reçue : {command}")
            if command.strip() == '':
                print("La commande est vide")
                return None
            return command
        except sr.UnknownValueError:
            print("Google Speech Recognition n'a pas compris ce que vous avez dit")
        except sr.RequestError as e:
            print(f"Une erreur s'est produite lors de la requête à l'API Google Speech Recognition ; {e}")

    return None
  
            
def load_api_key(file_path):
    with open(file_path, 'r') as file:
        api_key = file.read().strip()
    return api_key
    
def chat_with_gpt(prompt, api_key_file):

    if prompt is None:
        print('Nothing to request, prompt empty')
        return None
    
    # load OpenAI API credentials
    api_key = load_api_key(api_key_file)
    api_endpoint = 'https://api.openai.com/v1/chat/completions'

    # Set the desired parameters for the conversation
    model = 'gpt-3.5-turbo'
    max_tokens = 50

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

    # Send the request to the OpenAI API
    response = requests.post(api_endpoint, json=data, headers=headers)

    # Handle the response
    if response.status_code == 200:
        # Get the generated message from the API response
        messages = response.json()['choices'][0]['message']['content']
        return messages
    else:
        print(f'Request failed with status code {response.status_code}')
        return None


#credentials stored in key.text
messages = chat_with_gpt(get_voice_command(), 'key.txt')
print(messages)
