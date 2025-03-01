import json
import os

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class WolfieAgent:
    def __init__(self):
        """
        Initialize the WolfieAgent with Gemini API.
        """
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.registered_functions = {}  # Dictionary to store registered functions

    def register_function(self, function, name, description, parameters):
        """
        Register a function with its name, description, and parameters.
        """
        self.registered_functions[name] = {
            "function": function,
            "description": description,
            "parameters": parameters
        }

    def ask(self, user_input):
        """
        Ask the Gemini API to handle the request and determine if a registered function should be called.
        """
        prompt = f"""
        You are an AI assistant. The user has provided the following input:
        {user_input}

        Available functions:
        {json.dumps(self.registered_functions, indent=2)}

        Determine if the user's input requires calling one of the registered functions.
        If yes, respond with the function name and the required parameters in JSON format.
        If no, respond with a helpful message based on the input.
        """

        response = self.model.generate_content(prompt)
        response_text = response.text.strip()

        try:
            function_call = json.loads(response_text)
            function_name = function_call.get("function_name")
            parameters = function_call.get("parameters", {})

            if function_name in self.registered_functions:
                result = self.registered_functions[function_name]["function"](**parameters)
                return f"Function '{function_name}' executed successfully. Result: {result}"
            else:
                return f"Function '{function_name}' is not registered."
        except json.JSONDecodeError:
            return response_text

    def __call__(self, user_input):
        """
        Make the class callable for convenience.
        """
        return self.ask(user_input)
