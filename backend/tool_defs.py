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
                        "description": "Keys are unique requirement IDs. Values are objects with 'num_needed' (int) and 'courses' (list of course objects)."
                    }
                }
            },
            "required": []
        }
    }

get_course_info = {
        "type": "function",
        "function": {
            "name": "course_info",
            "description": "Get detailed information about a specific course including name, code, credits, description, prerequisites, and terms offered this year.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_number": {
                        "type": "string",
                        "description": "Course number (e.g., '161', '122A', '45C')"
                    },
                    "department": {
                        "type": "string",
                        "description": "Department code in uppercase without spaces. Examples: 'COMPSCI' (for CS/CompSci), 'I&CSCI' (for ICS), 'IN4MATX' (for Informatics), 'STATS' (for Statistics)"
                    }
                }
            },
            "required": []
        }
    }

remaining_requirements = {
    "type": "function",
    "function": {
        "name": "get_remaining_requirements",
        "description": """Get remaining graduation requirements breakdown.
        
        Returns requirements_breakdown showing:
        - For each requirement category, how many courses are needed
        - How many courses are available to choose from in that category
        - Sample courses from each category
        
        Note: Some courses may satisfy multiple categories. Actual total courses needed depends on strategic course selection during planning.""",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


next_quarter_plan = {
    "type": "function",
    "function": {
        "name": "plan_next_quarter",
        "description": """Get all courses student can take next quarter (prerequisites met, offered next quarter).

        Returns:
        - available_courses: Flat list of all valid courses with details
        - num_available: Number of available courses

        Each course includes: code, name, credits, description, difficulty, satisfies_requirement (unique requirement ID), num_needed (how many courses needed from that requirement).""",
        "parameters": {
            "type": "object",
            "properties": {
                "preferred_num_courses": {
                    "type": "integer",
                    "description": "Number of courses to select",
                    "default": 3
                }
            },
            "required": []
        }
    }
} 

start_graduation_planning_tool = {
    "type": "function",
    "function": {
        "name": "start_graduation_planning",
        "description": """Start a multi-quarter graduation planning session.

        Creates a session that tracks state across multiple quarters.
        Use this when user asks to plan their complete path to graduation.

        Always ask user:
        1. "When do you want to graduate?" (e.g., Spring 2027)
        2. "How many courses do you want to take per quarter?" (typically 3-5)
        3. "Do you have any specific interests or focus areas?" (optional, e.g., AI, web development,...)

        Returns:
        - session_id: Use this in all subsequent graduation planning calls
        - graduation_quarter: Quarter user plans to graduate at the end of
        - quarters_to_plan: List of quarters to plan (e.g., ["Fall 2025", "Winter 2026", "Spring 2026"])
        - quarters_remaining: Number of quarters remaining to plan
        - next_quarter: The first quarter to plan
        - message: summary of graduation planning to be done

        After starting, use get_graduation_plan_for_quarter to see available courses for each quarter.""",
        "parameters": {
            "type": "object",
            "properties": {
                "graduation_quarter": {
                    "type": "string",
                    "description": "Target graduation quarter (e.g., 'Spring 2026', 'Fall 2026')"
                },
                "user_interests": {
                    "type": "string",
                    "description": "Optional. User's interests or focus areas as comma-separated keywords ('artificial intelligence, machine learning, data science'). If provided, courses matching these interests will be prioritized."
                },
                "courses_per_quarter": {
                    "type": "integer",
                    "description": "Number of courses to take per quarter. Typically 3-5. Defaults to 3 if not specified."
                }
            },
            "required": ["graduation_quarter"]
        }
    }
}

get_graduation_plan_for_quarter_tool = {
    "type": "function",
    "function": {
        "name": "get_graduation_plan_for_quarter",
        "description": """Get auto-selected courses for a specific quarter during graduation planning.

        This function automatically selects courses for quarter:
        - Prioritizes requirement groups with fewer available courses
        - Matches courses to user interests (if provided during start_graduation_planning)
        - Ensures all requirement categories are addressed
        - Uses updated state from previous quarters

        Must be called after start_graduation_planning.

        Returns:
        - selected_courses: List of auto-selected course objects with code, name, credits, difficulty, satisfies_requirement, num_needed
        - num_selected: Number of courses selected
        - message: Summary of selection

        NOTE: This function automatically selects courses. You don't need to select them yourself.""",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID from start_graduation_planning"
                },
                "quarter_name": {
                    "type": "string",
                    "description": "Quarter to plan (e.g., 'Fall 2025')"
                }
            },
            "required": ["session_id", "quarter_name"]
        }
    }
}

add_quarter_to_plan_tool = {
    "type": "function",
    "function": {
        "name": "add_quarter_to_plan",
        "description": """Add selected courses for a quarter to the graduation plan.

        This updates the session state.

        Call this after get_graduation_plan_for_quarter with the courses it returned.

        Returns:
        - quarter_added: The quarter name
        - courses_added: Number of courses added
        - courses: List of added courses with code and name
        - total_units: Total units for this quarter
        - requirements_remaining: Whether graduation requirements are still unmet
        - next_quarter: Next quarter to plan (or None if done)
        - message: Summary message""",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID from start_graduation_planning"
                },
                "quarter_name": {
                    "type": "string",
                    "description": "Quarter being planned (e.g., 'Fall 2025')"
                },
                "selected_courses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "name": {"type": "string"},
                            "credits": {"type": "integer"},
                            "difficulty": {"type": "string"}
                        }
                    },
                    "description": "List of course objects (use courses from get_graduation_plan_for_quarter response)"
                }
            },
            "required": ["session_id", "quarter_name", "selected_courses"]
        }
    }
}

finish_graduation_plan_tool = {
    "type": "function",
    "function": {
        "name": "finish_graduation_plan",
        "description": """Finalize graduation planning and get complete summary.

        Returns:
        - graduation_quarter: Target graduation quarter
        - quarters_planned: Number of quarters in the plan
        - total_courses: Total number of courses
        - total_units: Total units across all quarters
        - plan: Array of quarters with their courses
        - requirements_remaining: Boolean indicating if requirements are still unmet

        IMPORTANT: Check requirements_remaining before claiming success. If true, the plan is incomplete.

        Call this after planning all quarters.""",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID from start_graduation_planning"
                }
            },
            "required": ["session_id"]
        }
    }
}

TOOLS = [
    rec_courses,
    get_course_info,
    next_quarter_plan,
    remaining_requirements,
    start_graduation_planning_tool,
    get_graduation_plan_for_quarter_tool,
    add_quarter_to_plan_tool,
    finish_graduation_plan_tool
]