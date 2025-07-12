"""
Skill Card Image Generator
Generates skill card images based on interview results

Installation requirements:
pip install google-genai

Environment variable required:
GOOGLE_API_KEY=your_gemini_api_key
"""
from datetime import datetime
import os
import base64
import mimetypes
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai not installed. Image generation will not be available.")

class SkillCardGenerator:
    """
    Generates skill card images using Google's Gemini API
    """
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.client = None
        if GENAI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # Create card images directory
        self.cards_dir = Path("card_images")
        self.cards_dir.mkdir(exist_ok=True)
        
        # Rarity mapping based on star ratings
        self.rarity_mapping = {
            5: "Legendary",
            4: "Epic", 
            3: "Rare",
            2: "Uncommon",
            1: "Common"
        }
    
    def _get_api_key(self) -> str:
        """Get API key from environment variable."""
        api_key = "AIzaSyB4YsVZrGEFdBZQzyLvMu0Oae4BlXedlks"
        if not api_key:
            logger.warning("GOOGLE_API_KEY environment variable not found.")
        return api_key
    
    def _save_binary_file(self, file_name: str, data: bytes) -> str:
        """Save binary data to a file in the cards directory."""
        file_path = self.cards_dir / file_name
        with open(file_path, "wb") as f:
            f.write(data)
        logger.info(f"Skill card saved to: {file_path}")
        return str(file_path)
    
    def _generate_prompt_and_description(self, skill_name: str, rarity_level: str) -> Dict[str, str]:
        """Generate both image prompt and skill description for the given skill and rarity level."""
        if not self.client:
            raise Exception("Gemini client not available. Check API key and installation.")
        
        model = "gemini-2.5-pro"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"Skill: {skill_name}\nRarity: {rarity_level}"),
                ],
            ),
        ]

        # Remove tools and use text/plain instead of application/json
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(text="""You are a prompt generator for trading card creation. Your task is to create both image generation prompts and skill descriptions for trading card games.

Requirements:
1. Generate an image prompt that shows someone demonstrating the specified skill
2. Use the color palette associated with the rarity level
3. Style should be clean digital illustration suitable for trading cards
4. Create a 2-3 line skill description that explains what this skill involves
5. Make the description engaging and suitable for a trading card game

Color palettes by rarity:
- Common: Gray, silver, muted tones
- Uncommon: Green, teal, fresh colors
- Rare: Blue, cyan, bright blues
- Epic: Purple, pink, magenta
- Legendary: Gold, orange, warm yellows

Return your response in this exact format:
IMAGE_PROMPT: Generate an image of [detailed scene description]. [Color palette instruction]. Style should be clean digital illustration suitable for a skill card. 300x160 aspect ratio, landscape orientation. No text or UI elements.

SKILL_DESCRIPTION: A 2-3 line description explaining what this skill involves and why it's valuable. Keep it concise and engaging for a trading card.

Now create both image prompt and description for:
Skill: {skill_name}
Rarity: {rarity_level}"""),
            ],
        )

        # Generate the prompt and description
        response_text = ""
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text

        # Parse the text response
        try:
            lines = response_text.strip().split('\n')
            image_prompt = ""
            skill_description = ""
            
            for line in lines:
                if line.startswith("IMAGE_PROMPT:"):
                    image_prompt = line.replace("IMAGE_PROMPT:", "").strip()
                elif line.startswith("SKILL_DESCRIPTION:"):
                    skill_description = line.replace("SKILL_DESCRIPTION:", "").strip()
            
            # Fallback if parsing fails
            if not image_prompt or not skill_description:
                logger.warning(f"Failed to parse response for {skill_name}, using fallback")
                return {
                    "image_prompt": f"Generate an image of someone demonstrating {skill_name} skills. Use {rarity_level.lower()} color palette. Style should be clean digital illustration suitable for a skill card. 300x160 aspect ratio, landscape orientation. No text or UI elements.",
                    "skill_description": f"Demonstrates proficiency in {skill_name}. A {rarity_level.lower()} skill that requires dedication and practice to master."
                }
            
            return {
                "image_prompt": image_prompt,
                "skill_description": skill_description
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse response for {skill_name}: {str(e)}, using fallback")
            return {
                "image_prompt": f"Generate an image of someone demonstrating {skill_name} skills. Use {rarity_level.lower()} color palette. Style should be clean digital illustration suitable for a skill card. 300x160 aspect ratio, landscape orientation. No text or UI elements.",
                "skill_description": f"Demonstrates proficiency in {skill_name}. A {rarity_level.lower()} skill that requires dedication and practice to master."
            }
    
    def _generate_image(self, prompt: str, skill_name: str, rarity_level: str, skill_description: str) -> Dict[str, str]:
        """Generate an image based on the prompt and save it."""
        if not self.client:
            raise Exception("Gemini client not available. Check API key and installation.")
        
        model = "gemini-2.0-flash-preview-image-generation"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
            response_mime_type="text/plain",
        )

        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue

            if (chunk.candidates[0].content.parts[0].inline_data and
                chunk.candidates[0].content.parts[0].inline_data.data):
                # Save the generated image
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"
                
                # Clean skill name for filename
                clean_skill_name = "".join(c for c in skill_name if c.isalnum() or c in (' ', '-', '_')).strip()
                clean_skill_name = clean_skill_name.replace(' ', '_')
                
                file_name = f"{clean_skill_name}_{rarity_level}_skillcard{file_extension}"
                file_path = self._save_binary_file(file_name, data_buffer)
                
                return {
                    "file_path": file_path,
                    "file_name": file_name,
                    "skill_description": skill_description
                }
            else:
                if chunk.text:
                    logger.info(f"Generation info: {chunk.text}")
        
        raise Exception("No image data received from API")
    
    def generate_skill_card(self, skill_name: str, star_rating: int) -> Dict[str, Any]:
        """
        Generate a single skill card image with description.
        
        Args:
            skill_name: Name of the skill
            star_rating: Star rating (1-5)
            
        Returns:
            Dictionary with generation results
        """
        try:
            # Map star rating to rarity
            rarity_level = self.rarity_mapping.get(star_rating, "Common")
            
            logger.info(f"Generating skill card for: {skill_name} ({star_rating} stars -> {rarity_level})")
            
            # Step 1: Generate the prompt and description
            logger.info("Generating prompt and description...")
            prompt_data = self._generate_prompt_and_description(skill_name, rarity_level)
            image_prompt = prompt_data["image_prompt"]
            skill_description = prompt_data["skill_description"]
            
            logger.info(f"Generated prompt: {image_prompt}")
            logger.info(f"Generated description: {skill_description}")
            
            # Step 2: Generate the image
            logger.info("Generating image...")
            image_data = self._generate_image(image_prompt, skill_name, rarity_level, skill_description)
            
            return {
                "success": True,
                "skill": skill_name,
                "star_rating": star_rating,
                "rarity": rarity_level,
                "file_path": image_data["file_path"],
                "file_name": image_data["file_name"],
                "skill_description": skill_description,  # This is the AI-generated description
                "prompt_used": image_prompt
            }
            
        except Exception as e:
            logger.error(f"Error generating card for {skill_name}: {str(e)}")
            return {
                "success": False,
                "skill": skill_name,
                "star_rating": star_rating,
                "error": str(e)
            }
    
    def generate_cards_from_interview_results(self, skill_ratings: Dict[str, int], interview_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate skill cards for all skills from interview results.
        
        Args:
            skill_ratings: Dictionary of skill names to star ratings
            interview_id: Optional interview ID for tracking
            
        Returns:
            Dictionary with generation results for all skills
        """
        if not GENAI_AVAILABLE:
            return {
                "success": False,
                "error": "google-genai package not installed. Please install it with: pip install google-genai"
            }
        
        if not self.api_key:
            return {
                "success": False,
                "error": "GOOGLE_API_KEY environment variable not set"
            }
        
        logger.info(f"Generating cards for {len(skill_ratings)} skills")
        
        results = {
            "success": True,
            "total_skills": len(skill_ratings),
            "generated_cards": [],
            "failed_cards": [],
            "cards_directory": str(self.cards_dir),
            "interview_id": interview_id
        }
        
        for skill_name, star_rating in skill_ratings.items():
            card_result = self.generate_skill_card(skill_name, star_rating)
            
            if card_result.get("success", False):
                results["generated_cards"].append(card_result)
                logger.info(f"✅ Generated card for {skill_name}")
            else:
                results["failed_cards"].append(card_result)
                logger.error(f"❌ Failed to generate card for {skill_name}")
        
        results["success_count"] = len(results["generated_cards"])
        results["failure_count"] = len(results["failed_cards"])
        
        # Save JSON mapping file if any cards were generated
        if results["generated_cards"]:
            try:
                json_file_path = self._save_card_mapping_json(results["generated_cards"], interview_id)
                results["mapping_file"] = json_file_path
                logger.info(f"📋 Card mapping saved to: {json_file_path}")
            except Exception as e:
                logger.error(f"Failed to save card mapping: {str(e)}")
                results["mapping_file_error"] = str(e)
        
        logger.info(f"Card generation complete: {results['success_count']} successful, {results['failure_count']} failed")
        
        # THIS WAS MISSING - Return the results!
        return results
    
    def _save_card_mapping_json(self, generated_cards: List[Dict[str, Any]], interview_id: Optional[int] = None) -> str:
        """
        Save a JSON file mapping image names to skill data.
        
        Args:
            generated_cards: List of successfully generated card data
            interview_id: Optional interview ID for unique naming
            
        Returns:
            Path to the saved JSON file
        """
        # Create mapping data
        card_mapping = {
            "generated_at": datetime.now().isoformat(),
            "interview_id": interview_id,
            "total_cards": len(generated_cards),
            "cards": {}
        }
        
        for card in generated_cards:
            file_name = card.get("file_name", "")
            card_mapping["cards"][file_name] = {
                "skill_name": card.get("skill", ""),
                "star_rating": card.get("star_rating", 0),
                "rarity": card.get("rarity", "Common"),
                "description": card.get("skill_description", ""),  # AI-generated description included here
                "file_path": card.get("file_path", ""),
                "prompt_used": card.get("prompt_used", "")
            }
        
        # Create JSON filename
        if interview_id:
            json_filename = f"skill_cards_interview_{interview_id}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"skill_cards_{timestamp}.json"
        
        json_file_path = self.cards_dir / json_filename
        
        # Save JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(card_mapping, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Card mapping saved to: {json_file_path}")
        return str(json_file_path)

# Convenience function for direct use
def generate_cards_for_interview(skill_ratings: Dict[str, int], interview_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to generate cards from interview results.
    
    Args:
        skill_ratings: Dictionary of skill names to star ratings (e.g., {"Python": 4, "Cooking": 3})
        interview_id: Optional interview ID for tracking
        
    Returns:
        Dictionary with generation results
    """
    generator = SkillCardGenerator()
    return generator.generate_cards_from_interview_results(skill_ratings, interview_id)