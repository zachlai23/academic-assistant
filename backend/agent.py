import openai
import anthropic
import os
import json
from dotenv import load_dotenv
import asyncio
from functions.course_functions import rec_degreeworks_courses, course_info
from typing import List, Dict
from tool_defs import TOOLS

# Store conversations between sessions
conversations = {}

async def agent(user_message: str, conversation_id: str, completed_courses: List[str], grad_reqs: Dict):
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

    When users mention courses, normalize department names, some examples are:
    - "cs", "comp sci", "compsci" → "COMPSCI"
    - "ics" → "I&CSCI"
    - "informatics", "inf" → "IN4MATX"
    - "stats", "statistics" → "STATS"

    Always use the formal department code when calling functions.
    """

    messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model= "gpt-3.5-turbo",
        messages= messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    if response.choices[0].message.tool_calls:
        print(response.choices[0].message.tool_calls[0])
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        function_args = tool_call.function.arguments 
        data = json.loads(function_args)

        if tool_name == "rec_degreeworks_courses":
            result = await rec_degreeworks_courses(completed_courses=completed_courses, grad_reqs=grad_reqs, major="Computer Science")
        elif tool_name == "course_info":
            result = await course_info(**data)
        else:
            result = {"error": f"unknown function {tool_name}"}

        print(result)

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