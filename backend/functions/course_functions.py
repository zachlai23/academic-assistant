
import json 
import asyncio
import os
from pprint import pprint

import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.parse_degreeworks import extract_courses_needed, extract_courses_completed

CURRENT_YEAR=2025
NEXT_QUARTER='2025 Winter'

# Returns list of courses that user can take based on prereqs + is required for graduation
async def rec_degreeworks_courses(completed_courses=None, grad_reqs=None, major="Computer Science"):
    course_recs = []
    # Loop through course requirements
    for requiredCt, courses in grad_reqs.items():
        for course in courses:
            if check_prereq(course, completed_courses):
                course_recs.append([course['code'], course['name'], course['description']])
    return course_recs

# Return the name, code, credits, description, prerequisites, difficulty, and offerings this year for a course in input
async def course_info(course_number, department):
    with open('data/courses.json', 'r') as f:
        data = json.load(f)
    # Loop through courses in department and find matching course, return info
    for course in data["courses"][department]:
        if course["code"] == f"{department}{course_number}":
            relevant_offerings = [
                quarter for quarter in course["offered_quarters"] 
                if int(quarter.split()[0]) >= CURRENT_YEAR
            ]
            return {
                "name": course["name"],
                "code": course["code"],
                "credits": course["credits"],
                "description": course["description"],
                "prerequisites": course["prerequisites"],
                "difficulty": course.get("difficulty", "unknown"),
                "offered_quarters": relevant_offerings
            }
    return {
        "error": f"Course {department}{course_number} not found"
    }

# Returns all courses user can take next quarter based on prereqs and offerings
# let ai decide from those recs for smarter recommendations
async def plan_next_quarter(completed_courses=None, grad_reqs=None, preferred_num_courses=3):
    possible_courses = defaultdict(list) # number required : list of courses
    possible_courses_ct = 0
    seen_codes = set()  
    all_possible_courses = []   # Flat list of courses user can take

    for numRequired, courses in grad_reqs.items():
        for course in courses:
            if (course['code'] not in seen_codes and 
                course['code'] not in completed_courses and 
                check_prereq(course, completed_courses) and 
                NEXT_QUARTER in course['offered_quarters']):

                possible_courses_ct += 1

                course_summary = {
                    "code": course['code'],
                    "name": course['name'],
                    "credits": course['credits'],
                    "description": course['description'],
                    "difficulty": course['difficulty']
                }
                possible_courses[numRequired].append(course_summary)
                all_possible_courses.append(course_summary)
                seen_codes.add(course['code'])

    if not possible_courses:
        return {
            "error": "No courses available for next quarter",
            "available_courses": []
        }
    
    return {
        "available_courses": all_possible_courses,
        "courses_by_requirement": dict(possible_courses),
        "num_available": len(all_possible_courses),
        "message": f"Found {len(all_possible_courses)} valid courses for next quarter. Select {preferred_num_courses} courses (aim for 12-18 total units)."
    }

# Return the remaining requirements a user needs to graduate
async def get_remaining_requirements(completed_courses=None, grad_reqs=None):
    requirements_breakdown = {}
    
    for num_required, courses in grad_reqs.items():
        # Filter out completed courses
        remaining_courses = [
            course for course in courses 
            if course["code"] not in completed_courses
        ]

        # For each section collect breakdown of requirements
        requirements_breakdown[num_required] = {
            "num_needed": int(num_required),
            "num_available": len(remaining_courses),
            "sample_courses": [c["code"] for c in remaining_courses[:5]]  # Show first 5 as examples
        }
    return {
        "requirements_breakdown": requirements_breakdown,
    }

# HELPER FUNCTIONS

# Checks if user can take given course based on prereqs
# Input is course object
def check_prereq(course, completed_courses=None):
    if completed_courses is None:
        completed_courses = []

    if not course["prerequisites"]:
        return True

    return check_prereq_tree(course["prereq_tree"], completed_courses)

# Recursive function to check if compelted courses satisfies prereq tree for a course
def check_prereq_tree(prereq_tree, completed_courses=None):
    if not prereq_tree:
        return True
    # Base case - if course taken return true, not handling exams for now
    if prereq_tree.get("prereqType") == "course":
        course_id = normalize_course_id(prereq_tree["courseId"])
        return course_id in completed_courses
    
    # AND - return true if all children in tree(courses or ORs) satisfied
    if prereq_tree.get("AND"):
        return all(check_prereq_tree(child, completed_courses) for child in prereq_tree["AND"])

    # OR - return true if any children in tree(courses or ORs) satisfied
    if prereq_tree.get("OR"):
        return any(check_prereq_tree(child, completed_courses) for child in prereq_tree["OR"])

    # Exams return false here, should be handled in project though
    return False

# Normalize course id's to remove spaces to match course codes
def normalize_course_id(course_id):
    return course_id.replace(' ', '').upper()

if __name__ == "__main__":
    import asyncio
    
    async def test():
        courses_completed = extract_courses_completed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
        courses_needed = extract_courses_needed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")

        q = await plan_next_quarter(completed_courses=courses_completed, grad_reqs=courses_needed, preferred_num_courses=3)
        pprint(q['available_courses'])
    
    asyncio.run(test())
