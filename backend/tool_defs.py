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

plan_quarter = {
        "type": "function",
        "function": {
            "name": "plan_quarter",
            "description": "Give a quarter plan based on completed courses, courses needed for graduation, and users preferred number of courses to take.",
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
                    "preferred_num_courses": {
                        "type": "integer", 
                        "description": "Preferred number of courses user wants to take next quarter.",
                        "default": 3
                    }
                }
            },
            "required": []
        }
    }

TOOLS = [rec_courses, get_course_info, plan_quarter]
