# Simple Jarvis: A Voice-based Chatbot with OpenAI 🗣️💬🤖

Welcome to Simple Jarvis, a voice-based chatbot utilizing Google's Speech Recognition service and OpenAI's GPT models. This project allows you to interact with a state-of-the-art language model using voice commands, which are translated into text and passed to the OpenAI API. 

The main script is easy to use and customizable, with options for setting the OpenAI model, maximum tokens for the response, and more.

## Getting Started 🚀

1. Clone the repository:

    ```
    git clone https://github.com/louispaulet/simple_jarvis.git
    cd simple_jarvis
    ```

2. Install the necessary Python libraries:

    ```
    pip install -r requirements.txt
    ```

3. Obtain an API key from OpenAI and save it in a file. By default, the script looks for the key in 'key.txt':

    ```
    echo 'your-api-key' > key.txt
    ```

4. Run the script and speak a command when prompted:

    ```
    python simple_jarvis.py
    ```

Optionally, you can specify the OpenAI model, maximum tokens, and API key file with command line arguments:

    ```
    python simple_jarvis.py --model gpt-3.5-turbo --max-tokens 100 --api-key-file mykey.txt
    ```

## Contributing 💡

We welcome contributions! Please feel free to submit a pull request with any improvements or bug fixes.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 👏

- Thanks to OpenAI for their amazing GPT models and API
- Thanks to Google for their Speech Recognition service
