"""
Updated Interviews API endpoints with automatic skill card generation
Cards are automatically generated when interview results are fetched
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime

from services.interview_service import InterviewService
from ml.response_evaluator import ResponseEvaluator
from database import execute_sql

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the skill card generator with detailed error logging
try:
    from ml.skill_card_generator import SkillCardGenerator
    CARD_GENERATION_AVAILABLE = True
    logger.info("✅ SkillCardGenerator imported successfully")
except ImportError as e:
    CARD_GENERATION_AVAILABLE = False
    logger.error(f"❌ Failed to import SkillCardGenerator: {e}")
except Exception as e:
    CARD_GENERATION_AVAILABLE = False
    logger.error(f"❌ Unexpected error importing SkillCardGenerator: {e}")

router = APIRouter()

# Models
class InterviewStart(BaseModel):
    candidate_name: Optional[str] = "Anonymous"
    skills: Optional[str] = "general skills"  # Skills to assess (comma-separated)
    skill_area: Optional[str] = "general"     # Category
    questions_per_skill: Optional[int] = 3    # Questions per skill

class InterviewResponse(BaseModel):
    question_id: int
    response: str

# Initialize components
interview_service = InterviewService()
response_evaluator = ResponseEvaluator()

# Initialize card generator with error checking
card_generator = None
if CARD_GENERATION_AVAILABLE:
    try:
        card_generator = SkillCardGenerator()
        logger.info("✅ SkillCardGenerator initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize SkillCardGenerator: {e}")
        CARD_GENERATION_AVAILABLE = False
        card_generator = None
else:
    logger.warning("⚠️ Card generation not available - check imports and dependencies")

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_skill_based_interview(interview: InterviewStart):
    """
    Start a new skill-based interview session
    """
    # Create interview record
    execute_sql(
        "INSERT INTO interviews (candidate_name, skill_area, status, created_at) VALUES (?, ?, ?, datetime('now'))",
        (interview.candidate_name, f"{interview.skill_area}: {interview.skills}", "pending")
    )
    
    # Get the new interview ID
    new_interview = execute_sql(
        "SELECT id FROM interviews ORDER BY created_at DESC LIMIT 1"
    )
    
    if not new_interview:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create interview"
        )
    
    interview_id = new_interview[0]["id"]
    
    # Generate skill-based questions
    await generate_skill_based_questions(
        interview_id, 
        interview.skills, 
        interview.skill_area,
        interview.questions_per_skill
    )
    
    return {
        "interview_id": interview_id,
        "message": "Skill-based interview started successfully",
        "skills_assessed": interview.skills,
        "questions_per_skill": interview.questions_per_skill,
        "next_step": f"/api/interviews/{interview_id}/questions"
    }

async def generate_skill_based_questions(
    interview_id: int, 
    skills: str, 
    skill_area: str,
    questions_per_skill: int = 3
):
    """
    Generate skill-specific questions with proper skill tracking
    """
    try:
        # Parse skills in order
        skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        # Create job description
        job_description = f"Assessment for skills: {', '.join(skill_list)}"
        
        # Generate questions for each skill in order
        all_questions = []
        skill_question_map = {}
        
        for skill_index, skill in enumerate(skill_list):
            # Generate 3 questions for this skill
            skill_questions = interview_service.question_generator.generate_skill_specific_questions(
                skill, job_description, questions_per_skill
            )
            
            # Track which questions belong to which skill
            start_index = len(all_questions)
            all_questions.extend(skill_questions)
            end_index = len(all_questions)
            
            skill_question_map[skill] = {
                "start_index": start_index,
                "end_index": end_index,
                "question_count": questions_per_skill,
                "questions_completed": 0
            }
        
        # Store questions in database with skill names and order
        for i, question_data in enumerate(all_questions):
            question_text = question_data["question"]
            skill = question_data["skill"]
            skill_index = question_data["skill_index"]
            
            # Store with actual skill name and question order
            execute_sql(
                "INSERT INTO interview_questions (interview_id, question, question_type, evaluation) VALUES (?, ?, ?, ?)",
                (interview_id, question_text, skill, json.dumps({
                    "skill": skill, 
                    "skill_index": skill_index,
                    "global_question_order": i + 1
                }))
            )
        
        # Store skill metadata in interview record
        skills_metadata = {
            "skills_assessed": skill_list,
            "questions_per_skill": questions_per_skill,
            "skill_question_map": skill_question_map,
            "total_questions": len(all_questions)
        }
        
        execute_sql(
            "UPDATE interviews SET status = 'active', feedback = ? WHERE id = ?",
            (json.dumps(skills_metadata), interview_id)
        )
        
    except Exception as e:
        execute_sql(
            "UPDATE interviews SET status = 'error', feedback = ? WHERE id = ?",
            (f"Error generating questions: {str(e)}", interview_id)
        )
        raise Exception(f"Failed to generate skill-based questions: {str(e)}")

@router.get("/{interview_id}/questions")
async def get_skill_based_interview_questions(interview_id: int):
    """
    Get all skill-based questions for an interview
    """
    # Check if interview exists
    interview = execute_sql(
        "SELECT * FROM interviews WHERE id = ?",
        (interview_id,)
    )
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    interview_data = interview[0]
    
    # Get questions with skill metadata
    questions = execute_sql(
        "SELECT id, question, question_type, response, score, evaluation FROM interview_questions WHERE interview_id = ? ORDER BY id",
        (interview_id,)
    )
    
    # Parse questions with skill information
    enhanced_questions = []
    for q in questions:
        question_info = {
            "id": q["id"],
            "question": q["question"],
            "question_type": q["question_type"],
            "response": q["response"],
            "score": q["score"]
        }
        
        # Parse skill metadata from evaluation field
        if q["evaluation"]:
            try:
                metadata = json.loads(q["evaluation"])
                if "skill" in metadata:
                    question_info["skill"] = metadata["skill"]
                    question_info["skill_index"] = metadata.get("skill_index", 1)
            except:
                pass
        
        enhanced_questions.append(question_info)
    
    # Parse skills metadata from interview feedback
    skills_info = {}
    if interview_data["feedback"]:
        try:
            skills_info = json.loads(interview_data["feedback"])
        except:
            pass
    
    return {
        "interview_id": interview_id,
        "candidate_name": interview_data["candidate_name"],
        "skill_area": interview_data["skill_area"],
        "status": interview_data["status"],
        "questions": enhanced_questions,
        "total_questions": len(enhanced_questions),
        "answered_questions": len([q for q in enhanced_questions if q["response"]]),
        "skills_assessed": skills_info.get("skills_assessed", []),
        "questions_per_skill": skills_info.get("questions_per_skill", 3),
        "skills_metadata": skills_info.get("skills_metadata", {})
    }

@router.post("/submit-response")
async def submit_skill_based_response(response: InterviewResponse):
    """
    Submit response and update skill rating if skill is complete
    """
    # Get question details
    question = execute_sql(
        "SELECT iq.*, i.id as interview_id, i.feedback as interview_metadata FROM interview_questions iq " +
        "JOIN interviews i ON iq.interview_id = i.id " +
        "WHERE iq.id = ?",
        (response.question_id,)
    )
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
        
    question_data = question[0]
    interview_id = question_data["interview_id"]
    
    # Get skill name from question_type field
    skill = question_data["question_type"]
    
    # Store the response
    execute_sql(
        "UPDATE interview_questions SET response = ? WHERE id = ?",
        (response.response, response.question_id)
    )
    
    # Evaluate the response
    evaluation_result = interview_service.evaluate_skill_response(
        question_data["question"],
        response.response,
        skill,
        "skill_specific"
    )
    
    evaluation = evaluation_result.get("evaluation", {})
    
    # Store evaluation
    evaluation_json = json.dumps(evaluation)
    execute_sql(
        "UPDATE interview_questions SET evaluation = ?, score = ? WHERE id = ?",
        (evaluation_json, evaluation.get("score", 0), response.question_id)
    )
    
    # Check if this skill is now complete and update its rating
    skill_rating_update = await check_and_update_skill_rating(interview_id, skill)
    
    # Check overall interview completion
    all_questions = execute_sql(
        "SELECT count(*) as total FROM interview_questions WHERE interview_id = ?",
        (interview_id,)
    )[0]["total"]
    
    answered_questions = execute_sql(
        "SELECT count(*) as answered FROM interview_questions WHERE interview_id = ? AND response IS NOT NULL",
        (interview_id,)
    )[0]["answered"]
    
    interview_completed = (all_questions == answered_questions)
    
    if interview_completed:
        # Mark interview as completed
        execute_sql(
            "UPDATE interviews SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
            (interview_id,)
        )
    
    return {
        "question_id": response.question_id,
        "evaluation": evaluation,
        "skill_assessed": skill,
        "skill_rating_update": skill_rating_update,
        "interview_progress": {
            "answered": answered_questions,
            "total": all_questions,
            "completed": interview_completed
        },
        "next_step": f"/api/interviews/{interview_id}/results" if interview_completed else "Continue to next question"
    }

async def check_and_update_skill_rating(interview_id: int, skill: str) -> dict:
    """
    Check if a skill is complete (3 questions answered) and update its rating
    """
    # Get all questions for this skill in this interview
    skill_questions = execute_sql(
        "SELECT score FROM interview_questions WHERE interview_id = ? AND question_type = ? AND response IS NOT NULL",
        (interview_id, skill)
    )
    
    total_skill_questions = execute_sql(
        "SELECT count(*) as total FROM interview_questions WHERE interview_id = ? AND question_type = ?",
        (interview_id, skill)
    )[0]["total"]
    
    answered_skill_questions = len(skill_questions)
    
    # If all questions for this skill are answered, calculate rating
    if answered_skill_questions == total_skill_questions and answered_skill_questions > 0:
        # Calculate average score for this skill
        scores = [q["score"] for q in skill_questions if q["score"] is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
            star_rating = convert_score_to_stars(avg_score)
            
            # Store skill rating in a new table or update interview feedback
            await store_skill_rating(interview_id, skill, star_rating, avg_score)
            
            return {
                "skill": skill,
                "completed": True,
                "star_rating": star_rating,
                "average_score": round(avg_score, 1),
                "questions_answered": answered_skill_questions
            }
    
    return {
        "skill": skill,
        "completed": False,
        "questions_answered": answered_skill_questions,
        "questions_total": total_skill_questions
    }

async def store_skill_rating(interview_id: int, skill: str, star_rating: int, avg_score: float):
    """
    Store individual skill rating in database
    """
    # Get existing interview feedback
    interview = execute_sql(
        "SELECT feedback FROM interviews WHERE id = ?",
        (interview_id,)
    )[0]
    
    # Parse existing feedback
    feedback_data = {}
    if interview["feedback"]:
        try:
            feedback_data = json.loads(interview["feedback"])
        except:
            feedback_data = {}
    
    # Add skill ratings section
    if "skill_ratings" not in feedback_data:
        feedback_data["skill_ratings"] = {}
    
    feedback_data["skill_ratings"][skill] = {
        "star_rating": star_rating,
        "average_score": avg_score,
        "completed_at": datetime.now().isoformat()
    }
    
    # Update interview feedback
    execute_sql(
        "UPDATE interviews SET feedback = ? WHERE id = ?",
        (json.dumps(feedback_data), interview_id)
    )

async def auto_generate_skill_cards(interview_id: int, skill_ratings: Dict[str, int]) -> Dict[str, Any]:
    """
    Automatically generate skill cards in the background and create JSON mapping
    """
    # Debug logging
    logger.info(f"🎨 Card generation requested for interview {interview_id}")
    logger.info(f"🎯 Skill ratings: {skill_ratings}")
    
    if not CARD_GENERATION_AVAILABLE:
        logger.warning("❌ CARD_GENERATION_AVAILABLE is False")
        return {
            "cards_generated": False,
            "reason": "Card generation not available - import failed"
        }
    
    if card_generator is None:
        logger.warning("❌ card_generator is None")
        return {
            "cards_generated": False,
            "reason": "Card generator not initialized"
        }
    
    try:
        logger.info("🚀 Starting card generation...")
        
        # Setup directories
        import os
        import time
        from pathlib import Path
        cards_dir = Path("card_images")
        cards_dir.mkdir(exist_ok=True)
        
        # Record start time to identify new files
        start_time = time.time()
        
        # Generate cards using your current generator
        generation_results = card_generator.generate_cards_from_interview_results(skill_ratings)
        
        # Wait a moment for file system to update
        time.sleep(1)
        
        # Find recently created PNG files
        new_files = []
        if cards_dir.exists():
            for file_path in cards_dir.glob("*.png"):
                file_mod_time = os.path.getmtime(file_path)
                if file_mod_time >= start_time - 5:  # Files created in last 5 seconds
                    new_files.append(file_path)
        
        logger.info(f"🔍 Found {len(new_files)} recently created files: {[f.name for f in new_files]}")
        
        # Rarity mapping
        rarity_mapping = {
            5: "Legendary",
            4: "Epic", 
            3: "Rare",
            2: "Uncommon",
            1: "Common"
        }
        
        # Create the JSON mapping
        card_mapping = {
            "generated_at": datetime.now().isoformat(),
            "interview_id": interview_id,
            "total_cards": 0,
            "cards": {}
        }
        
        generated_cards = []
        failed_cards = []
        
        # Process each skill
        for skill_name, star_rating in skill_ratings.items():
            expected_rarity = rarity_mapping.get(star_rating, "Common")
            
            # Clean skill name for filename matching
            clean_skill = "".join(c for c in skill_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            
            # Try different possible filename formats
            possible_filenames = [
                f"{clean_skill}_{expected_rarity}_skillcard.png",
                f"{skill_name.replace(' ', '_')}_{expected_rarity}_skillcard.png",
                f"{skill_name.replace(' ', '')}_{expected_rarity}_skillcard.png"
            ]
            
            logger.info(f"🔎 Looking for {skill_name} with possible names: {possible_filenames}")
            
            # Find matching file
            found_file = None
            for file_path in new_files:
                if file_path.name in possible_filenames:
                    found_file = file_path
                    break
                # Also try partial matching
                if any(clean_skill.lower() in file_path.name.lower() and expected_rarity.lower() in file_path.name.lower() for clean_skill in [clean_skill, skill_name.replace(' ', '_'), skill_name.replace(' ', '')]):
                    found_file = file_path
                    break
            
            if found_file:
                logger.info(f"✅ Found file for {skill_name}: {found_file.name}")
                
                # Generate skill description
                if star_rating == 5:
                    skill_description = f"Master-level expertise in {skill_name}. This legendary skill demonstrates exceptional proficiency and deep understanding."
                elif star_rating == 4:
                    skill_description = f"Advanced proficiency in {skill_name}. This epic skill shows strong capabilities and experience."
                elif star_rating == 3:
                    skill_description = f"Solid competence in {skill_name}. This rare skill indicates good knowledge and practical ability."
                elif star_rating == 2:
                    skill_description = f"Basic proficiency in {skill_name}. This uncommon skill shows foundational understanding."
                else:
                    skill_description = f"Entry-level knowledge in {skill_name}. This common skill represents initial learning and experience."
                
                # Add to mapping
                card_mapping["cards"][found_file.name] = {
                    "skill_name": skill_name,
                    "star_rating": star_rating,
                    "rarity": expected_rarity,
                    "description": skill_description,
                    "file_path": str(found_file),
                    "prompt_used": f"AI-generated visualization of {skill_name} expertise at {expected_rarity} level"
                }
                
                generated_cards.append({
                    "success": True,
                    "skill": skill_name,
                    "star_rating": star_rating,
                    "rarity": expected_rarity,
                    "file_path": str(found_file),
                    "file_name": found_file.name,
                    "skill_description": skill_description
                })
                
            else:
                logger.warning(f"❌ No file found for {skill_name}")
                failed_cards.append({
                    "success": False,
                    "skill": skill_name,
                    "star_rating": star_rating,
                    "error": f"No matching file found. Expected patterns: {possible_filenames}"
                })
        
        # Update total count
        card_mapping["total_cards"] = len(generated_cards)
        
        # Save JSON mapping file
        json_filename = f"skill_cards_interview_{interview_id}.json"
        json_file_path = cards_dir / json_filename
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(card_mapping, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Card mapping saved to: {json_file_path}")
        logger.info(f"📊 Mapping contains {len(card_mapping['cards'])} cards")
        
        # Log the mapping content for debugging
        for file_name, card_data in card_mapping["cards"].items():
            logger.info(f"   📄 {file_name}: {card_data['skill_name']} ({card_data['rarity']})")
        
        # Create response
        manual_results = {
            "success": True,
            "cards_generated": True,
            "success_count": len(generated_cards),
            "failure_count": len(failed_cards),
            "total_skills": len(skill_ratings),
            "generated_cards": generated_cards,
            "failed_cards": failed_cards,
            "cards_directory": str(cards_dir),
            "mapping_file": str(json_file_path),
            "interview_id": interview_id
        }
        
        logger.info(f"✅ Card generation completed: {manual_results['success_count']} successful, {manual_results['failure_count']} failed")
        
        # Store generation results in interview record
        interview = execute_sql(
            "SELECT feedback FROM interviews WHERE id = ?",
            (interview_id,)
        )[0]
        
        feedback_data = {}
        if interview["feedback"]:
            try:
                feedback_data = json.loads(interview["feedback"])
            except:
                feedback_data = {}
        
        feedback_data["card_generation"] = {
            "generated_at": datetime.now().isoformat(),
            "results": manual_results,
            "mapping_file_content": card_mapping  # Store the mapping in the database too
        }
        
        execute_sql(
            "UPDATE interviews SET feedback = ? WHERE id = ?",
            (json.dumps(feedback_data), interview_id)
        )
        
        return {
            "cards_generated": True,
            "success_count": manual_results["success_count"],
            "failure_count": manual_results["failure_count"],
            "cards_directory": manual_results["cards_directory"],
            "mapping_file": manual_results["mapping_file"],
            "generated_cards": manual_results["generated_cards"],
            "mapping_content": card_mapping  # Include the mapping content in the response
        }
        
    except Exception as e:
        # Log error but don't fail the response
        logger.error(f"💥 Error generating cards for interview {interview_id}: {str(e)}")
        return {
            "cards_generated": False,
            "reason": f"Generation failed: {str(e)}"
        }
                        
@router.get("/{interview_id}/results")
async def get_interview_results_with_auto_cards(interview_id: int):
    """
    Get interview results and automatically generate skill cards
    """
    logger.info(f"📊 Getting results for interview {interview_id}")
    
    # Get interview
    interview = execute_sql(
        "SELECT * FROM interviews WHERE id = ?",
        (interview_id,)
    )
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
        
    interview_data = interview[0]
    
    # Parse skill ratings from feedback
    skill_ratings = {}
    feedback_data = {}
    
    if interview_data["feedback"]:
        try:
            feedback_data = json.loads(interview_data["feedback"])
            if "skill_ratings" in feedback_data:
                # Extract just the star ratings
                for skill, rating_data in feedback_data["skill_ratings"].items():
                    skill_ratings[skill] = rating_data["star_rating"]
        except:
            pass
    
    # If no stored skill ratings, calculate on the fly
    if not skill_ratings:
        logger.info("🔄 Calculating skill ratings on the fly...")
        questions = execute_sql(
            "SELECT question_type, score FROM interview_questions WHERE interview_id = ? AND response IS NOT NULL",
            (interview_id,)
        )
        
        skill_scores = {}
        for q in questions:
            skill = q["question_type"]
            score = q["score"] or 0
            
            if skill not in skill_scores:
                skill_scores[skill] = []
            skill_scores[skill].append(score)
        
        for skill, scores in skill_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                skill_ratings[skill] = convert_score_to_stars(avg_score)
    
    logger.info(f"🎯 Final skill ratings: {skill_ratings}")
    
    # Calculate overall rating
    if skill_ratings:
        overall_stars = round(sum(skill_ratings.values()) / len(skill_ratings))
        overall_score = overall_stars * 2  # Convert stars to score approximation
    else:
        overall_stars = 1
        overall_score = 1
    
    # AUTO-GENERATE SKILL CARDS (if not already generated)
    card_generation_info = None
    if skill_ratings:
        logger.info(f"🎨 Checking card generation availability...")
        
        # Check if cards were already generated
        cards_already_generated = False
        if "card_generation" in feedback_data:
            cards_already_generated = True
            card_generation_info = feedback_data["card_generation"]
            logger.info("✅ Cards already generated previously")
        
        if not cards_already_generated and CARD_GENERATION_AVAILABLE and card_generator is not None:
            logger.info("🚀 Attempting to auto-generate cards...")
            try:
                card_generation_info = await auto_generate_skill_cards(interview_id, skill_ratings)
            except Exception as e:
                logger.error(f"💥 Auto-generation failed: {str(e)}")
                card_generation_info = {
                    "cards_generated": False,
                    "reason": f"Auto-generation failed: {str(e)}"
                }
        elif not CARD_GENERATION_AVAILABLE:
            logger.warning("⚠️ Card generation not available")
            card_generation_info = {
                "cards_generated": False,
                "reason": "Card generation not available - check imports and API key"
            }
        elif card_generator is None:
            logger.warning("⚠️ Card generator not initialized")
            card_generation_info = {
                "cards_generated": False,
                "reason": "Card generator not initialized"
            }
    else:
        logger.warning("⚠️ No skill ratings available for card generation")
    
    # Prepare response
    response_data = {
        "interview_id": interview_id,
        "candidate_name": interview_data["candidate_name"],
        "status": interview_data["status"],
        "completed_at": interview_data["completed_at"],
        "skill_ratings": skill_ratings,  # Python: 4, Cooking: 3, Public Speaking: 5
        "overall_score": overall_score,
        "overall_stars": overall_stars,
        "total_skills": len(skill_ratings)
    }
    
    # Add card generation info if available
    if card_generation_info:
        response_data["card_generation"] = card_generation_info
    
    # Add debug info for troubleshooting
    response_data["debug"] = {
        "card_generation_available": CARD_GENERATION_AVAILABLE,
        "card_generator_initialized": card_generator is not None,
        "skill_ratings_found": len(skill_ratings) > 0
    }
    
    logger.info(f"📤 Returning response with card generation info: {card_generation_info}")
    return response_data

def convert_score_to_stars(score: float) -> int:
    """
    Convert 1-10 score to 1-5 star rating
    """
    if score >= 9:
        return 5
    elif score >= 7:
        return 4
    elif score >= 5:
        return 3
    elif score >= 3:
        return 2
    else:
        return 1
        
@router.get("/list")
async def list_recent_interviews(limit: int = 10):
    """
    List recent interviews with skill information
    """
    interviews = execute_sql(
        "SELECT id, candidate_name, skill_area, status, score, created_at, completed_at " +
        "FROM interviews ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    
    # Enhance with skill information
    enhanced_interviews = []
    for interview in interviews:
        enhanced_interview = dict(interview)
        
        # Count questions for this interview
        question_count = execute_sql(
            "SELECT count(*) as total FROM interview_questions WHERE interview_id = ?",
            (interview["id"],)
        )[0]["total"]
        
        enhanced_interview["total_questions"] = question_count
        enhanced_interviews.append(enhanced_interview)
    
    return {
        "interviews": enhanced_interviews,
        "count": len(enhanced_interviews)
    }