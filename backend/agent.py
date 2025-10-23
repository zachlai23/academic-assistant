import openai
import anthropic
import os
import json
from dotenv import load_dotenv
import asyncio
from functions.course_functions import rec_degreeworks_courses
from typing import List, Dict

# Store conversations between sessions
conversations = {}

async def agent(user_message: str, conversation_id: str, completed_courses: List[str], grad_reqs: Dict):
    # Move to separate file eventually
    rec_courses = {
        "type": "function",
        "function": {
            "name": "rec_degreeworks_courses",
            "description": "Recommends courses based on the classes the user has already taken and classes needed for graduation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed_courses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of course codes the student completed.(format: COMPSCI171 with no spaces)"
                    },
                    "grad_reqs": {
                        "type": "object",
                        "description": "Keys are number of courses needed from the value list to satisfy the degree.  Values are lists of course objects."
                    },
                    "major": {
                        "type": "string",
                        "description": "Student's major"
                    }
                }
            },
            "required": []
        }
    }

    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("CLAUDEAI_API_KEY") # Move over to Anthropic API

    client = openai.AsyncOpenAI(api_key=openai_api_key)

    if conversation_id in conversations:
        messages = conversations[conversation_id].copy()
    else:
        messages = []

    system_message = """You are an academic advisor helping students plan their courses.

    The student has uploaded their DegreeWorks with their completed courses and graduation requirements.
    When they ask for course recommendations, use the rec_degreeworks_courses function.
    """

    messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model= "gpt-3.5-turbo",
        messages= messages,
        tools=[rec_courses],
        tool_choice="auto"
    )

    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        function_args = tool_call.function.arguments 
        data = json.loads(function_args)
        result = await rec_degreeworks_courses(completed_courses=completed_courses, grad_reqs=grad_reqs, major="Computer Science")

        messages.append({
            "role": "assistant", 
            "content": None,
            "tool_calls": [{
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }]
        })   
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})

        final_response = await client.chat.completions.create(
            model= "gpt-3.5-turbo",
            messages= messages
        )

        conversations[conversation_id] = messages

        return final_response.choices[0].message.content
    else:
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        conversations[conversation_id] = messages
        return response.choices[0].message.content

if __name__ == "__main__":
    asyncio.run(agent())