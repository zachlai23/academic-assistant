import uuid
from collections import defaultdict
from typing import List, Dict, Any
from functions.course_functions import plan_next_quarter

graduation_sessions = {}

# Graduation planning continually calls quarter plan function while keeping track of classes added/remaining requirements
# saves state for graduation planning
class GraduationSession:

    def __init__(self, original_completed, original_grad_reqs, graduation_quarter, quarters_to_plan, user_interests=None, courses_per_quarter=3):
        self.original_completed = original_completed.copy()
        # Deep copy
        self.original_grad_reqs = {
            k: {
                "num_needed": v["num_needed"],
                "courses": v["courses"].copy()
            } for k, v in original_grad_reqs.items()
        }
        self.graduation_quarter = graduation_quarter
        self.planned_quarters = []
        self.current_completed = original_completed.copy()
        self.current_grad_reqs = {
            k: {
                "num_needed": v["num_needed"],
                "courses": v["courses"].copy()
            } for k, v in original_grad_reqs.items()
        }
        self.next_quarter = "Winter 2026"
        self.quarters_to_plan = quarters_to_plan
        self.user_interests = user_interests
        self.courses_per_quarter = courses_per_quarter


    # update class instance completed/grad reqs after a quarter is planned
    def add_quarter(self, quarter_name, courses):
        self.planned_quarters.append({
            "quarter": quarter_name,
            "courses": courses
        })
        
        # update completed courses
        for course in courses:
            self.current_completed.append(course["code"])
        
        # update grad requirements
        self.current_grad_reqs = update_requirements(self.current_grad_reqs, courses)

    # Returns complete graduation plan summary
    def get_summary(self):
        total_courses = sum(len(q["courses"]) for q in self.planned_quarters)
        total_units = sum(sum(c.get("credits", 4) for c in q["courses"]) for q in self.planned_quarters)
        
        return {
            "graduation_quarter": self.graduation_quarter,
            "quarters_planned": len(self.planned_quarters),
            "total_courses": total_courses,
            "total_units": total_units,
            "plan": self.planned_quarters,
            "requirements_remaining": len(self.current_grad_reqs) > 0
        }

# Takes in quarter name, returns next quarter
def get_next_quarter(curr_quarter):
    parts = curr_quarter.split()
    season, year = parts[0], int(parts[1])

    if season == "Fall":
        return f"Winter {year + 1}"
    elif season == "Winter":
        return f"Spring {year}"
    elif season == "Spring":
        return f"Fall {year}"
    return None

# returns updated grad_reqs after planning courses for graduation
def update_requirements(grad_reqs, planned_courses):
    updated_reqs = {}
    planned_codes = [course["code"] for course in planned_courses]

    # each item in form req_id:{num_needed, courses}
    for req_id, req_data in grad_reqs.items():
        num_needed = req_data["num_needed"]
        courses = req_data["courses"]

        # remove planned courses
        remaining = [c for c in courses if c["code"] not in planned_codes]

        # update num required
        num_satisfied = len([c for c in courses if c["code"] in planned_codes])
        new_required = num_needed - num_satisfied

        # keep updated requirement in dict if still needed
        if new_required > 0 and remaining:
            updated_reqs[req_id] = {
                "num_needed": new_required,
                "courses": remaining
            }

    return updated_reqs
 
# Initialize grad planning session - create session id + class instance
# Returns dict with session id and planning info
async def start_graduation_planning(graduation_quarter, completed_courses, grad_reqs, user_interests=None, courses_per_quarter=3):
    session_id = str(uuid.uuid4())[:8]

    curr_quarter = "Winter 2026"
    quarters_until = 0
    quarters_to_plan = []

    while curr_quarter != graduation_quarter:
        quarters_until += 1
        quarters_to_plan.append(curr_quarter)
        curr_quarter = get_next_quarter(curr_quarter)

    quarters_to_plan.append(graduation_quarter)
    quarters_until += 1

    if quarters_until <= 0:
        return {"error": f"Graduation quarter is invalid or in the past"}

    # Create graduation session
    session = GraduationSession(completed_courses, grad_reqs, graduation_quarter, quarters_to_plan, user_interests, courses_per_quarter)
    graduation_sessions[session_id] = session

    return {
        "session_id": session_id,
        "graduation_quarter": graduation_quarter,
        "quarters_to_plan": quarters_to_plan,
        "quarters_remaining": quarters_until,
        "next_quarter": quarters_to_plan[0] if quarters_to_plan else None,
        "message": f"Started planning for {graduation_quarter}. Plan {quarters_until} quarters with {courses_per_quarter} courses per quarter. Start with {quarters_to_plan[0]}."
    }

# Call quarter plan function with the updated completed courses/grad reqs
async def add_quarter_to_plan(session_id, quarter_name, selected_courses):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}
    
    session = graduation_sessions[session_id]
    
    # Error/duplicate validation
    already_planned = [
        c["code"] for q in session.planned_quarters for c in q["courses"]
    ]

    for course in selected_courses:
        if course["code"] in already_planned:
            return {"error": f"{course['code']} already planned"}
    
    session.add_quarter(quarter_name, selected_courses)
    
    # bool for if grad requirements satisfied
    requirements_met = len(session.current_grad_reqs) == 0
    
    if quarter_name == session.graduation_quarter:
        session.next_quarter = None
    else:
        session.next_quarter = get_next_quarter(quarter_name)
    
    return {
        "quarter_added": quarter_name,
        "courses_added": len(selected_courses),
        "courses": [{"code": c["code"], "name": c["name"]} for c in selected_courses],
        "total_units": sum(c.get("credits", 4) for c in selected_courses),
        "requirements_remaining": not requirements_met,
        "next_quarter": session.next_quarter,
        "message": f"Added {len(selected_courses)} courses for {quarter_name}."
    }

# Select courses based on requirement groups
async def get_graduation_plan_for_quarter(session_id, quarter_name):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}

    session = graduation_sessions[session_id]

    courses_needed = session.courses_per_quarter

    # Returns all possible courses user can take
    all_available = await plan_next_quarter(
        completed_courses=session.current_completed,
        grad_reqs=session.current_grad_reqs,
        preferred_num_courses=courses_needed,
        single_q_planning=False
    )

    if "error" in all_available:
        return all_available

    selected_courses = smart_course_selection(
        all_available["available_courses"],
        session.current_grad_reqs,
        courses_needed,
        user_interests=session.user_interests
    )

    return {
        "selected_courses": selected_courses,
        "num_selected": len(selected_courses),
        "message": f"Auto-selected {len(selected_courses)} courses for {quarter_name}"
    }

# Helper function to calculate user interest similarity to course description using keyword matching
def calculate_interest_score(course, user_interests):
    if not user_interests:
        return 0

    # Convert to lowercase
    interests_lower = user_interests.lower()
    course_desc_lower = course.get("description", "").lower()
    course_name_lower = course.get("name", "").lower()

    # Count keyword matches - similarity can be improved using embeddings
    score = 0
    interest_keywords = [kw.strip() for kw in interests_lower.split(",")]

    for keyword in interest_keywords:
        # word matches course name
        if keyword in course_name_lower:
            score += 10
        # word matches course description
        if keyword in course_desc_lower:
            score += 5

    return score

# Select courses based on requirement groups, prioritize satisfying all requirements
def smart_course_selection(available_courses, grad_reqs, num_courses, user_interests=None):
    selected = []

    # Group courses by requirement id
    courses_by_requirement = {}
    for course in available_courses:
        req_id = course.get("satisfies_requirement")
        if req_id not in courses_by_requirement:
            courses_by_requirement[req_id] = []
        courses_by_requirement[req_id].append(course)

    # Sort courses within each requirement by interest match if user has interests
    if user_interests:
        for req_id in courses_by_requirement:
            courses_by_requirement[req_id] = sorted(
                courses_by_requirement[req_id],
                key=lambda c: calculate_interest_score(c, user_interests),
                reverse=True
            )

    # track how many courses we still needed from each requirement
    requirements_tracker = {}
    for req_id, req_data in grad_reqs.items():
        if req_id in courses_by_requirement:
            requirements_tracker[req_id] = {
                "num_needed": req_data["num_needed"],
                "num_selected": 0
            }

    # Sort requirement groups by number of courses available for requirement(higher priority)
    # and courses needed from requirement(less priority) for ties
    requirement_priority = sorted(
        courses_by_requirement.keys(),
        key=lambda req_id: (
            len(courses_by_requirement[req_id]),
            -requirements_tracker.get(req_id, {}).get("num_needed", 0)
        )
    )

    # Select 1 course from each requirement first
    for req_id in requirement_priority:
        if len(selected) >= num_courses:
            break

        num_needed = requirements_tracker.get(req_id, {}).get("num_needed", 1)

        # Get courses from requirement that aren't selected yet
        req_courses = [
            c for c in courses_by_requirement[req_id]
            if c["code"] not in [s["code"] for s in selected]
        ]

        # Select up to num_needed courses from this requirement or until limit is reached
        for i in range(min(num_needed, len(req_courses))):
            if len(selected) >= num_courses:
                break
            selected.append(req_courses[i])
            requirements_tracker[req_id]["num_selected"] += 1

    # Fill remaining slots with highest priority unsatisfied requirements while courses still needed - shouldnt be used often
    while len(selected) < num_courses:
        remaining = [
            c for c in available_courses
            if c["code"] not in [s["code"] for s in selected]
        ]
        if not remaining:
            break

        # Find unsatisfied requirements
        unsatisfied_reqs = [
            req_id for req_id in requirement_priority
            if requirements_tracker.get(req_id, {}).get("num_selected", 0) <
               requirements_tracker.get(req_id, {}).get("num_needed", 0)
        ]

        # Fill from unsatisfied requirements first
        added = False
        for req_id in unsatisfied_reqs:
            req_courses = [c for c in remaining if c.get("satisfies_requirement") == req_id]
            if req_courses:
                selected.append(req_courses[0])
                requirements_tracker[req_id]["num_selected"] += 1
                added = True
                break

        # If no requirements needed pick from any remaining course
        if not added:
            selected.append(remaining[0])
            break

    return selected

# get final summary of grad plan
async def finish_graduation_plan(session_id):
    if session_id not in graduation_sessions:
        return {"error": "Session not found"}
    
    session = graduation_sessions[session_id]
    summary = session.get_summary()
    
    del graduation_sessions[session_id]
    
    return summary