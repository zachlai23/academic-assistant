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
        - courses_by_requirement: Courses grouped by requirement (key = number needed for graduation from that group)
        
        Select the best combination based on: student interest, required courses first, student preferred units or 12-18 units total.""",
        "parameters": {
            "type": "object",
            "properties": {
                "preferred_num_courses": {
                    "type": "integer",
                    "description": "Number of courses to select",
                    "default": 4
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
        
        Returns:
        - session_id: Use this in all subsequent graduation planning calls
        - quarters_to_plan: List of quarters to plan (e.g., ["Fall 2025", "Winter 2026", "Spring 2026"])
        - next_quarter: The first quarter to plan
        
        After starting, use get_graduation_plan_for_quarter to see available courses for each quarter.""",
        "parameters": {
            "type": "object",
            "properties": {
                "graduation_quarter": {
                    "type": "string",
                    "description": "Target graduation quarter (e.g., 'Spring 2026', 'Fall 2026')"
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
        "description": """Get available courses for a specific quarter during graduation planning.
        
        This uses the session's updated state - courses planned in previous quarters
        are treated as completed when checking prerequisites.
        
        Must be called AFTER start_graduation_planning.
        
        Returns same format as plan_next_quarter but with updated prerequisites.""",
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
        
        This updates the session state:
        - Adds courses to current_completed (for prerequisite checking in future quarters)
        - Updates grad_reqs (removes satisfied requirements)
        - Tracks the quarter in the plan
        
        Call this AFTER selecting courses from get_graduation_plan_for_quarter.
        
        Returns info about next quarter to plan.""",
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
                    "description": "List of course objects selected for this quarter (must include code, name, credits)"
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
        - Complete quarter-by-quarter plan
        - Total courses and units
        - Whether requirements are met
        
        Call this after planning all quarters or when requirements are satisfied.""",
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