
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


# Returns all courses user can take next quarter based on prereqs and offerings
# let ai decide from those recs for smarter recommendations
async def plan_next_quarter(completed_courses=None, grad_reqs=None, preferred_num_courses=3):
    possible_courses = defaultdict(list) # number required : list of courses
    possible_courses_ct = 0
    seen_codes = set()  
    all_possible_courses = []   # Flat list of courses user can take

    for numRequired, courses in grad_reqs.items():
        for course in courses:
            if course['code'] not in seen_codes and check_prereq(course, completed_courses) and NEXT_QUARTER in course['offered_quarters']:
                possible_courses_ct += 1

                course_summary = {
                    "code": course['code'],
                    "name": course['name'],
                    "credits": course['credits'],
                    "description": course['description']
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

# HELPER FUNCTIONS

# Return the remaining requirements a user needs to graduate
# Number of quarters according to preferred classes per quarter
# Total number of courses needed
async def get_remaining_requirements(completed_courses=None, grad_reqs=None, preferred_classes_per_quarter=4):
    totalCourses = 0
    for requiredCt, courses in grad_reqs.items():
        totalCourses += requiredCt
        pprint(requiredCt, ": ", courses)
    print("Courses needed for graduation: ", totalCourses)

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
        # course_info_returned = await course_info(116, "COMPSCI")
        # print(course_info_returned)
        # with open('../data/courses.json', 'r') as f:
        #     data = json.load(f)

        courses_completed = extract_courses_completed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")
        courses_needed = extract_courses_needed("/Users/zacharylai/Desktop/zach_degreeworks.pdf")

        next_quarter_plan = await plan_next_quarter(courses_completed, courses_needed, 3)
        pprint(next_quarter_plan)
        # courses = await rec_degreeworks_courses(courses_completed)

        # pprint(courses)
    
    asyncio.run(test())
