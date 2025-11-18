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

TOOLS = [rec_courses, get_course_info, next_quarter_plan, remaining_requirements]
