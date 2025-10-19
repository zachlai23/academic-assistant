
import json 
import asyncio
import os

# Course selection functions for llm to call

# Recommends courses based on completed courses
# Recommend courses with more prereqs completed
# Calculate score - higher score = better recommendation, sort based on score and return top 3

# Loop through all courses
# Call scoring function
# Sort courses descending by score
# Return top 3 courses

#SCORING FUNCTION
# Input: course object, prereqs -  Output: score
# if course already completed, score -1, move on
# if not all prereqs met, score 0, move on
# if all prereqs met, +1 for each prereq met

async def recommend_courses(completed_courses=None, major="Computer Science", num_recommendations=3):
    course_recs = []
    with open('data/courses.json', 'r') as file:
        data = json.load(file)

        if completed_courses == None:
            completed_courses = []
        
        print("Completed courses: ", completed_courses)

        courses_to_score = await possible_courses(data, completed_courses) # Find courses user passes prereqs for

        print(f"Possible Courses: {[course['code'] for course in courses_to_score]}")
        # Loop through each possible course
        for possible_course in courses_to_score:
            score = await course_scoring(completed_courses, possible_course)
            course_recs.append((score, [possible_course['code'], possible_course['name'], possible_course['description']]))

        # Sort courses descending by score
        course_recs.sort(reverse=True, key=lambda x: x[0])

        # Return top 3 courses
        return course_recs[:num_recommendations]

async def course_scoring(completed_courses=None, course=None):
    if completed_courses is None:
        completed_courses = []

    score = sum(1 for prereq in course['prerequisites'] if prereq in completed_courses)
    return score

# Checks if user can take given course based on prereqs
def can_take_course(course, completed_courses=None):
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
        # Load a course to test with
        with open('../data/courses.json', 'r') as f:
            data = json.load(f)

        print(possible_courses(data, ['COMPSCI171', 'COMPSCI178'])[0]['code'])
            
        # # Test with CS 175 (requires CS 101)
        # cs175 = next(c for c in data['courses'] if c['code'] == 'COMPSCI175')
        
        # # Test case 1: Student has CS 101
        # result1 = can_take_course(cs175, ['COMPSCI171', 'COMPSCI178'])
        # print(f"Can take CS 175 with CS 171 completed: {result1}")  # Should be True
        
        # # Test case 2: Student doesn't have prerequisites  
        # result2 = can_take_course(cs175, [])
        # print(f"Can take CS 175 with no courses: {result2}")  # Should be False

        # # Test case 1: Student has CS 101
        # result3 = can_take_course(cs175, ['COMPSCI171'])
        # print(f"Can take CS 175 with CS 171 completed, but not 178: {result3}")  # Should be False
    
    asyncio.run(test())
