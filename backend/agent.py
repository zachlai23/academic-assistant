import openai
import anthropic
import os
import json
from dotenv import load_dotenv
import asyncio
from functions.course_functions import rec_degreeworks_courses, course_info, plan_next_quarter, get_remaining_requirements
from typing import List, Dict
from tool_defs import TOOLS

# Store conversations between sessions
conversations = {}

async def agent(user_message: str, conversation_id: str, completed_courses: List[str], grad_reqs: Dict):
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")

    client = openai.AsyncOpenAI(api_key=openai_api_key)

    if conversation_id in conversations:
        messages = conversations[conversation_id].copy()
    else:
        messages = []

    system_message = """You are an academic advisor helping students plan their courses.

    The student has uploaded their DegreeWorks with their completed courses and graduation requirements.

    **Available tools:**
    - get_remaining_requirements: Check what requirements remain to graduate (shows breakdown by category)
    - plan_next_quarter: Get all valid courses for a specific quarter (call multiple times for graduation planning)
    - course_info: Get detailed information about a specific course
    - rec_degreeworks_courses: Get general course recommendations

    **For single quarter planning:**
    When asked to plan one quarter:
    1. Ask the user: "How many courses would you like to take next quarter?" (typical range: 3-5 courses)
    2. Call plan_next_quarter with their preferred number
    3. Select the best courses from available options based on: required courses first, balanced difficulty, and student preferences
    4. Present the plan with course codes, names, total units, and brief reasoning

    **Department name normalization:**
    When users mention courses, normalize department names:
    - "cs", "comp sci", "compsci" → "COMPSCI"
    - "ics" → "I&CSCI"
    - "informatics", "inf" → "IN4MATX"
    - "stats", "statistics" → "STATS"

    Always use the formal department code when calling functions.
    """

    messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model= "gpt-4o-mini",
        messages= messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        function_args = tool_call.function.arguments 
        data = json.loads(function_args)

        if tool_name == "rec_degreeworks_courses":
            result = await rec_degreeworks_courses(completed_courses=completed_courses, grad_reqs=grad_reqs, major="Computer Science")
        elif tool_name == "course_info":
            result = await course_info(**data)
        elif tool_name == "plan_next_quarter":
            result = await plan_next_quarter(
                completed_courses=completed_courses,
                grad_reqs=grad_reqs,
                preferred_num_courses=data.get("preferred_num_courses", 4)
            )
        elif tool_name == "get_remaining_requirements":
            result = await get_remaining_requirements(
                completed_courses=completed_courses,
                grad_reqs=grad_reqs
            )
        else:
            result = {"error": f"unknown function {tool_name}"}

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