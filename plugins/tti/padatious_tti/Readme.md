


# Padatious TTI Plugin for Naomi

## Overview

The **Padatious TTI Plugin** is a powerful natural language understanding (NLU) component designed for the Naomi platform. It uses the Padatious intent recognition engine to interpret spoken language commands and map them to intents. This plugin enhances Naomi’s ability to process user input using a trained neural network model, enabling highly accurate intent classification.

The plugin’s primary function is to analyze user speech, identify intents through text-to-intent (TTI) recognition, and return relevant actions based on predefined intent sets. This makes it an integral part of voice-controlled applications, allowing Naomi to become a more intelligent and adaptive voice assistant.

## Key Features

- **Efficient Intent Recognition**: Leverages Padatious, a neural network-based intent recognition engine, to understand user commands and associate them with the appropriate responses or actions.
- **Training and Customization**: Supports training new intents from user input, making it flexible to adapt to different use cases and commands.
- **Seamless Integration**: Fully compatible with the Naomi platform, allowing easy integration into existing voice-controlled setups.
- **Multilingual Support**: Offers the ability to support multiple languages depending on the training data provided.
- **Lightweight and Fast**: Designed to run efficiently even on low-resource devices while maintaining high accuracy for intent classification.

## Requirements

### APT Requirements:
- `libfann-dev`
- `python3-dev`
- `python3-pip`
- `swig`
- `libfann-dev`
- `python3-fann2`

### Python Requirements:
- `padatious`

These dependencies ensure that the necessary libraries and tools for neural network training and intent recognition are properly set up.

## Installation

1. **Clone the Repository**: Clone the padatious TTI plugin repository from GitHub:
   ```bash
   git clone https://github.com/NaomiProject/naomi-plugin-padatious-tti.git
   ```

2. **Install Required Dependencies**: Install the necessary packages by running:
   ```bash
   sudo apt-get install libfann-dev python3-dev python3-pip swig libfann-dev python3-fann2
   pip install padatious
   ```

3. **Add to Naomi Configuration**: Once installed, configure the plugin within the Naomi framework by updating the plugin directory with the path to the padatious-tti plugin.

## Usage

1. **Training Intents**: Define custom intents for specific commands. You can train the model by adding training data, which associates various phrases with corresponding actions.

   Example of intent training data:
   ```plaintext
   [greeting]
   hello
   hi there
   good morning
   ```

2. **Intent Classification**: After training, the plugin processes user input and matches it to the most likely intent. For example, a user can say “Hi,” and the plugin will classify this as a greeting intent.

3. **Testing**: The plugin includes a `test_padatious_tti.py` file to ensure that intent recognition is working as expected. You can run this file to verify that your intents are being correctly classified.

## Contributing

Contributions are welcome! If you would like to contribute to the development of this plugin, feel free to open a pull request on GitHub. Ensure that your code follows the project’s guidelines and includes appropriate test cases.

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Add your changes, and ensure all tests pass.
4. Open a pull request with a clear description of your changes.

## License

This plugin is licensed under the MIT License. See the LICENSE file for more details.

## Example Usage in Naomi

Once installed and configured, the Padatious TTI Plugin enables Naomi to recognize natural language commands. For instance, when a user says:

- **User**: “Turn on the lights.”
- **Naomi**: Recognizes the ‘turn on lights’ intent and sends a signal to the connected home automation system to turn on the lights.

This plugin plays a crucial role in making Naomi’s interactions more natural and intuitive for users, whether it’s for smart home control, entertainment systems, or general voice-command tasks.

This detailed description is meant to serve as a robust guide for using and contributing to the Padatious TTI Plugin.
```

