import openai
import anthropic
import os
import json
from dotenv import load_dotenv
import asyncio
from functions.course_functions import rec_degreeworks_courses

# Store conversations between sessions
conversations = {}

async def agent(user_message: str, conversation_id: str):
    # Move to separate file eventually
    rec_courses = {
        "type": "function",
        "function": {
            "name": "recommend_courses",
            "description": "Recommends courses based on the classes the user has already taken.",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed_courses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of course codes the student completed.(format: COMPSCI171 with no spaces)"
                    },
                    "major": {
                        "type": "string",
                        "description": "Student's major"
                    },
                    "num_recommendations": {
                        "type": "integer",
                        "description": "number of courses recommendations to return."
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
        result = await recommend_courses(**data)

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