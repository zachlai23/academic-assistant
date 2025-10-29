
import json 
import asyncio
import os
from pprint import pprint

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.parse_degreeworks import extract_courses_needed, extract_courses_completed

CURRENT_YEAR=2025

# Returns list of courses that user can take based on prereqs + is required for graduation
async def rec_degreeworks_courses(completed_courses=None, grad_reqs=None, major="Computer Science"):
    # courses_grad_reqs = extract_courses_needed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
    course_recs = []
    # Loop through course requirements
    for requiredCt, courses in grad_reqs.items():
        for course in courses:
            if check_prereq(course, completed_courses):
                course_recs.append([course['code'], course['name'], course['description']])
    return course_recs

# Return the name, code, credits, description, prerequisites, and offerings this year for a course in input
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
            return [course["name"], course["code"], course["credits"], course["description"], course["prerequisites"], relevant_offerings]


# HELPER FUNCTIONS

# Checks if user can take given course based on prereqs
# Input is course object
def check_prereq(course, completed_courses=None):
    if completed_courses is None:
        completed_courses = []
    return all(prereq in completed_courses for prereq in course['prerequisites'])

# Returns all courses user can take based on their completed courses
async def possible_courses(course_data, completed_courses):
    courses_can_take = []

    for course in course_data['courses']:
        
        if (len(course['prerequisites']) > 0 
            and course['code'] not in completed_courses 
            and all(prereq in completed_courses for prereq in course['prerequisites'])):
            courses_can_take.append(course)
    return courses_can_take

if __name__ == "__main__":
    import asyncio
    
    async def test():
        course_info_returned = await course_info(116, "COMPSCI")
        print(course_info_returned)
        # with open('../data/courses.json', 'r') as f:
        #     data = json.load(f)

        # courses_completed = extract_courses_completed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")

        # pprint(courses_completed)

        # courses = await rec_degreeworks_courses(courses_completed)

        # pprint(courses)
    
    asyncio.run(test())
