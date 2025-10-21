
import json 
import asyncio
import os
from pprint import pprint

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.parse_degreeworks import parse_degreeworks

# Returns list of courses that user can take based on prereqs + is required for graduation
async def rec_degreeworks_courses(completed_courses=None, major="Computer Science"):
    courses_grad_reqs = parse_degreeworks("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
    course_recs = []

    # Loop through course requirements
    for requiredCt, courses in courses_grad_reqs.items():
        for course_list in courses:
            for course in course_list:
                if check_prereq(course, completed_courses):
                    course_recs.append([course['code'], course['name'], course['description']])

    return course_recs

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
        with open('../data/courses.json', 'r') as f:
            data = json.load(f)

        courses = await rec_degreeworks_courses(["I&CSCI6D",
                "MATH3A",
                "I&CSCI6N",
                "MATH2B",
                "I&CSCI46",
                "CSE46",
                "COMPSCI112",
                "COMPSCI116",
                "COMPSCI171",
                "COMPSCI178"])

        pprint(courses)
    
    asyncio.run(test())
