from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import DeepSeek

class DeepSeekAgent:
    def __init__(self, api_key):
        """
        Initialize the DeepSeekAgent with an API key.
        """
        self.api_key = api_key
        self.llm = DeepSeek(api_key=api_key)  # Initialize DeepSeek LLM
        self.registered_functions = {}  # Dictionary to store registered functions

    def register_function(self, function_name, function, description, parameters):
        """
        Register a function with its name, description, and parameters.
        """
        self.registered_functions[function_name] = {
            "function": function,
            "description": description,
            "parameters": parameters
        }

    def ask(self, user_input):
        """
        Ask the DeepSeek API to handle the request and determine if a registered function should be called.
        """
        # Step 1: Determine if a function should be called
        prompt = PromptTemplate(
            input_variables=["user_input", "functions"],
            template="""
            You are an AI assistant. The user has provided the following input:
            {user_input}

            Available functions:
            {functions}

            Determine if the user's input requires calling one of the registered functions.
            If yes, respond with the function name and the required parameters in JSON format.
            If no, respond with a helpful message based on the input.
            """
        )

        # Format the available functions for the prompt
        functions_info = "\n".join([
            f"{name}: {info['description']} (Parameters: {info['parameters']})"
            for name, info in self.registered_functions.items()
        ])

        # Create the LLMChain
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(user_input=user_input, functions=functions_info)

        # Step 2: Parse the response to determine if a function should be called
        try:
            # Check if the response is a JSON string indicating a function call
            import json
            function_call = json.loads(response)
            function_name = function_call.get("function_name")
            parameters = function_call.get("parameters")

            if function_name in self.registered_functions:
                # Call the registered function
                result = self.registered_functions[function_name]["function"](**parameters)
                return f"Function '{function_name}' executed successfully. Result: {result}"
            else:
                return f"Function '{function_name}' is not registered."
        except json.JSONDecodeError:
            # If the response is not a JSON string, return it as is
            return response

    def __call__(self, user_input):
        """
        Make the class callable for convenience.
        """
        return self.ask(user_input)