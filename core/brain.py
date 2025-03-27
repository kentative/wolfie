import json
import logging.config
import os

import google.generativeai as genai
from dotenv import load_dotenv
from google.ai.generativelanguage_v1beta import ToolConfig
from google.generativeai import GenerationConfig

from utils.logger import init_logger

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

logger = init_logger('Brain')

class Brain:
    def __init__(self):
        """
        Initialize the WolfieAgent with Gemini API.
        """
        self.model = genai.GenerativeModel("gemini-2.0-flash")
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

    def get_tool_declarations(self):
        """
        Get the tool declarations for the registered functions in the required format.
        Returns a list containing a single dictionary with function_declarations.
        """
        function_declarations = []
        for name, function_info in self.registered_functions.items():
            required = []
            properties = {}
            for param_name, param_obj in function_info["parameters"].items():

                properties[param_name] = {
                    "type": "string",
                    "description": param_obj.description
                }
                if param_obj.required:
                    required.append(param_name)


            parameters = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                } if properties else None

            function_declarations.append({
                "name": name,
                "description": function_info["description"],
                "parameters": parameters
            })
        logger.info(json.dumps(function_declarations))

        return {
            "function_declarations" : function_declarations
        }

    async def ask(self, ctx, user_details: str, shared_events: str, interactions: str, user_input: str):
        """
        Ask the Gemini API to handle the request and determine if a registered function should be called.
        """

        # Construct the system prompt
        prompt = f"""
        Your name is Wolfie, an AI wolf companion for one of the strongest alliances in the game Age of Empires Mobile.
        You are part of the alliance known as TLW (TheLastWolves). Your goal is to provide helpful, concise,
        and accurate answers when asked. When interacting with members, you can relax, have fun, and play along.
        When you give a command example, don't include the parameter names.

        These are the alliance event details:
        {shared_events}

        This is the current user information:
        {user_details}

        You are provided with the following interaction history:
        {interactions}      

        Question:
        {user_input}       
        """

        response = self.model.generate_content(
            prompt,
            generation_config=GenerationConfig(temperature=0),
            tools=[self.get_tool_declarations()],
            tool_config=ToolConfig(
                function_calling_config= {
                    "mode" : "ANY"
                }
            )
        )

        # Check if a function call is suggested
        if response.parts and response.parts[0].function_call:
            function_call = response.parts[0].function_call
            function_name = function_call.name
            arguments = function_call.args
            logger.info(f"{function_name} called with arguments: {arguments}")

            # Execute the corresponding function if registered
            if function_name in self.registered_functions:
                function_output = await self.registered_functions[function_name]["function"](ctx, **arguments)
                return function_output

        # Return text response if no function call was made
        return response.text.strip()

    def ask_with_function(self, user_input: str):
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
