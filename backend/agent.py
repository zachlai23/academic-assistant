import openai
import anthropic
import os
import json
from dotenv import load_dotenv
import asyncio
from functions.course_functions import rec_degreeworks_courses, course_info, plan_next_quarter, get_remaining_requirements
from functions.graduation_planning import start_graduation_planning, get_graduation_plan_for_quarter, add_quarter_to_plan, finish_graduation_plan
from typing import List, Dict
from tool_defs import TOOLS

# Store conversations between sessions
conversations = {}

async def agent(user_message, conversation_id, completed_courses, grad_reqs):
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
    - get_remaining_requirements: Check what requirements remain to graduate
    - plan_next_quarter: Get all valid courses for a specific quarter (single quarter planning)
    - course_info: Get detailed information about a specific course
    - rec_degreeworks_courses: Get general course recommendations
    - start_graduation_planning: Initialize multi-quarter graduation planning session
    - get_graduation_plan_for_quarter: Get available courses for a quarter (with updated prerequisites from session)
    - add_quarter_to_plan: Add selected courses to graduation plan and update state
    - finish_graduation_plan: Get final graduation plan summary

    **Course difficulty:**
    Each course includes a difficulty rating(easy, medium, hard, unknown) based on historical GPA.

    **For single quarter planning:**
    When asked to plan one quarter:
    1. Ask the user how many classes they want to take (usually 3-5) and desired difficulty.
    2. Call plan_next_quarter
    3. Select courses based on requirements and difficulty preference
    4. Present plan with reasoning

    **For graduation planning:**
    1. Ask: "When do you graduate?".
    2. Call start_graduation_planning(graduation_quarter)
    3. For each quarter:
        a. Call get_graduation_plan_for_quarter(session_id, quarter_name)
            - Function automatically selects optimal courses
        b. Call add_quarter_to_plan(session_id, quarter_name, selected_courses)
            →-Use the selected_courses from step a
    4. Call finish_graduation_plan(session_id)
    5. Present complete plan

    CRITICAL: The final plan must satisfy all requirements.

    **Department name normalization:**
    - "cs", "comp sci", "compsci" -> "COMPSCI"
    - "ics" -> "I&CSCI"
    - "informatics", "inf" -> "IN4MATX"
    - "stats", "statistics" -> "STATS"
    """

    messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    # Loop until agent stops calling tools, eliminates filler messages while multi quarter planning
    max_iters = 15
    for iteration in range(max_iters):
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        
        # if agent wants to call tool
        if assistant_message.tool_calls:
            # Add tool calls to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in assistant_message.tool_calls]})
            
            # Execute all tool calls
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                function_args = tool_call.function.arguments
                data = json.loads(function_args)

                # execute tool
                if tool_name == "rec_degreeworks_courses":
                    result = await rec_degreeworks_courses(completed_courses=completed_courses, grad_reqs=grad_reqs)
                elif tool_name == "course_info":
                    result = await course_info(**data)
                elif tool_name == "plan_next_quarter":
                    result = await plan_next_quarter(
                        completed_courses=completed_courses,
                        grad_reqs=grad_reqs,
                        preferred_num_courses=data.get("preferred_num_courses", 4)
                    )
                elif tool_name == "get_remaining_requirements":
                    result = await get_remaining_requirements(completed_courses=completed_courses, grad_reqs=grad_reqs)
                elif tool_name == "start_graduation_planning":
                    result = await start_graduation_planning(
                        graduation_quarter=data.get("graduation_quarter"),
                        completed_courses=completed_courses,
                        grad_reqs=grad_reqs
                    )
                elif tool_name == "get_graduation_plan_for_quarter":
                    result = await get_graduation_plan_for_quarter(
                        session_id=data.get("session_id"),
                        quarter_name=data.get("quarter_name")
                    )
                elif tool_name == "add_quarter_to_plan":
                    result = await add_quarter_to_plan(
                        session_id=data.get("session_id"),
                        quarter_name=data.get("quarter_name"),
                        selected_courses=data.get("selected_courses", [])
                    )
                elif tool_name == "finish_graduation_plan":
                    result = await finish_graduation_plan(session_id=data.get("session_id"))
                else:
                    result = {"error": f"unknown function {tool_name}"}

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            continue
        
        else:
            # no more tool calls - return final message
            final_content = assistant_message.content
            messages.append({"role": "assistant", "content": final_content})
            conversations[conversation_id] = messages
            return final_content
    
    # If max iters hit
    return "Graduation plpanning issude. Please try again."

if __name__ == "__main__":
    asyncio.run(agent())