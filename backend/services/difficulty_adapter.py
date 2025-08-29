"""
Adaptive Difficulty System
Provides age-appropriate explanations and content adaptation
"""

import re
from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass

class DifficultyLevel(Enum):
    KID = "kid"        # 👶 Age 8-12: Simple explanations with examples/stories
    TEEN = "teen"      # 🧑 Age 13-17: Moderate difficulty
    COLLEGE = "college" # 🎓 Age 18+: Technical depth

@dataclass
class AdaptiveResponse:
    original_query: str
    difficulty_level: DifficultyLevel
    adapted_response: str
    key_concepts: List[str]
    examples_used: List[str]
    reading_level: str

class DifficultyAdapter:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.adaptation_templates = self._load_adaptation_templates()
        self.concept_library = self._load_concept_library()
    
    def _load_adaptation_templates(self) -> Dict[str, Dict]:
        """Load templates for different difficulty levels"""
        return {
            "kid": {
                "style": "Simple, fun, with stories and analogies",
                "vocabulary": "Use everyday words, avoid jargon",
                "examples": "Real-world examples kids can relate to",
                "length": "Keep explanations short and engaging",
                "tone": "Friendly, encouraging, like talking to a curious child",
                "prompt_suffix": """
                Explain this like you're talking to a smart 10-year-old. Use:
                - Simple words they know
                - Fun comparisons (like comparing atoms to LEGO blocks)
                - Short sentences
                - Exciting examples from their world
                - Encouraging tone
                """
            },
            "teen": {
                "style": "Clear, relatable, with practical applications",
                "vocabulary": "Mix of everyday and academic terms with explanations",
                "examples": "Technology, sports, social media analogies",
                "length": "Moderate detail with good structure",
                "tone": "Respectful, engaging, like a cool teacher",
                "prompt_suffix": """
                Explain this for a teenager (13-17 years old). Use:
                - Clear, straightforward language
                - Examples from technology, games, or daily life
                - Explain why it matters to them
                - Good structure with main points
                - Respectful but engaging tone
                """
            },
            "college": {
                "style": "Technical, comprehensive, with depth",
                "vocabulary": "Academic and scientific terminology",
                "examples": "Research studies, real applications, case studies",
                "length": "Detailed explanations with nuance",
                "tone": "Professional, scholarly, intellectually stimulating",
                "prompt_suffix": """
                Provide a college-level explanation. Include:
                - Proper scientific/academic terminology
                - Detailed mechanisms and processes
                - Current research and applications
                - Multiple perspectives or theories
                - Critical thinking prompts
                """
            }
        }
    
    def _load_concept_library(self) -> Dict[str, Dict]:
        """Library of how to explain common concepts at different levels"""
        return {
            "atom": {
                "kid": "Atoms are like tiny LEGO blocks that make up everything around you - your toys, your food, even you! Just like you can build different things with different LEGO pieces, atoms stick together to make different stuff.",
                "teen": "Atoms are the smallest units of matter that still keep the properties of an element. Think of them like the basic building blocks of everything - similar to how all your apps are made of basic code, everything physical is made of atoms.",
                "college": "Atoms are the fundamental units of matter consisting of a nucleus containing protons and neutrons, surrounded by electrons in quantum orbitals. They maintain the chemical properties of elements and combine through various bonding mechanisms."
            },
            "photosynthesis": {
                "kid": "Photosynthesis is how plants eat! They use sunlight like we use food for energy. Plants take in air and water, mix them with sunshine, and make their own food - plus they give us fresh air to breathe!",
                "teen": "Photosynthesis is the process where plants convert sunlight, carbon dioxide, and water into glucose (sugar) for energy, releasing oxygen as a bonus. It's basically nature's solar power system that also cleans our air.",
                "college": "Photosynthesis is a complex biochemical process involving light-dependent reactions in thylakoids and the Calvin cycle in chloroplast stroma, converting light energy into chemical energy stored in glucose while releasing oxygen."
            },
            "gravity": {
                "kid": "Gravity is an invisible force that pulls things down to Earth. It's why when you drop your toy, it falls to the ground instead of floating away like in space!",
                "teen": "Gravity is a fundamental force that attracts objects with mass toward each other. The more massive an object, the stronger its gravitational pull - that's why planets orbit the sun and we stay stuck to Earth.",
                "college": "Gravity is a fundamental interaction described by Einstein's General Relativity as the curvature of spacetime caused by mass and energy, governing planetary motion, stellar evolution, and cosmological structure."
            }
        }
    
    def adapt_explanation(self, content: str, difficulty: DifficultyLevel, topic: str = "") -> AdaptiveResponse:
        """
        Adapt content explanation to the specified difficulty level
        
        Args:
            content: Original content to adapt
            difficulty: Target difficulty level
            topic: Specific topic being explained (optional)
        
        Returns:
            AdaptiveResponse with adapted content
        """
        
        # Check if we have a pre-made explanation for common concepts
        if topic.lower() in self.concept_library:
            concept_explanation = self.concept_library[topic.lower()][difficulty.value]
            return AdaptiveResponse(
                original_query=content,
                difficulty_level=difficulty,
                adapted_response=concept_explanation,
                key_concepts=[topic],
                examples_used=self._extract_examples(concept_explanation),
                reading_level=self._estimate_reading_level(difficulty)
            )
        
        # Generate adaptive explanation using AI
        template = self.adaptation_templates[difficulty.value]
        
        prompt = f"""
        Adapt this educational content for {difficulty.value} level students:
        
        Original content: {content}
        
        {template['prompt_suffix']}
        
        Guidelines:
        - Style: {template['style']}
        - Vocabulary: {template['vocabulary']}
        - Examples: {template['examples']}
        - Length: {template['length']}
        - Tone: {template['tone']}
        
        Provide the adapted explanation:
        """
        
        try:
            adapted_content = self.ai_engine.generate_response(prompt)
            key_concepts = self._extract_key_concepts(adapted_content)
            examples = self._extract_examples(adapted_content)
            
            return AdaptiveResponse(
                original_query=content,
                difficulty_level=difficulty,
                adapted_response=adapted_content,
                key_concepts=key_concepts,
                examples_used=examples,
                reading_level=self._estimate_reading_level(difficulty)
            )
            
        except Exception as e:
            print(f"Error adapting content: {e}")
            # Fallback to original content
            return AdaptiveResponse(
                original_query=content,
                difficulty_level=difficulty,
                adapted_response=content,
                key_concepts=[],
                examples_used=[],
                reading_level="Unknown"
            )
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from adapted text"""
        # Simple keyword extraction - could be enhanced with NLP
        import re
        
        # Look for capitalized terms and scientific words
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter common words
        common_words = {'The', 'This', 'That', 'When', 'Where', 'Why', 'How', 'What'}
        concepts = [c for c in concepts if c not in common_words]
        
        return list(set(concepts))[:5]  # Return unique concepts, max 5
    
    def _extract_examples(self, text: str) -> List[str]:
        """Extract examples and analogies from text"""
        examples = []
        
        # Look for common example patterns
        example_patterns = [
            r'like (.+?)(?:\.|,|\n)',
            r'for example[,:]? (.+?)(?:\.|,|\n)',
            r'such as (.+?)(?:\.|,|\n)',
            r'imagine (.+?)(?:\.|,|\n)',
            r'think of (.+?)(?:\.|,|\n)'
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            examples.extend(matches)
        
        return examples[:3]  # Return first 3 examples
    
    def _estimate_reading_level(self, difficulty: DifficultyLevel) -> str:
        """Estimate reading level based on difficulty"""
        level_map = {
            DifficultyLevel.KID: "Grade 3-5 (Elementary)",
            DifficultyLevel.TEEN: "Grade 8-10 (High School)",
            DifficultyLevel.COLLEGE: "Grade 13+ (College/University)"
        }
        return level_map[difficulty]
    
    def get_age_appropriate_examples(self, concept: str, difficulty: DifficultyLevel) -> List[str]:
        """Get age-appropriate examples for a concept"""
        
        example_sets = {
            "kid": {
                "energy": ["running around the playground", "a toy car battery", "eating food for strength"],
                "molecules": ["LEGO blocks stuck together", "ingredients in a recipe", "puzzle pieces"],
                "ecosystem": ["a fish tank with fish and plants", "your backyard with birds and bugs", "a forest with animals and trees"]
            },
            "teen": {
                "energy": ["phone battery power", "car engine fuel", "solar panels charging devices"],
                "molecules": ["apps made of code lines", "teams made of players", "songs made of notes"],
                "ecosystem": ["social media networks", "gaming communities", "school social groups"]
            },
            "college": {
                "energy": ["ATP in cellular respiration", "potential vs kinetic energy systems", "thermodynamic processes"],
                "molecules": ["protein folding mechanisms", "chemical bond formation", "molecular orbital theory"],
                "ecosystem": ["population dynamics models", "trophic cascade effects", "biodiversity indices"]
            }
        }
        
        concept_lower = concept.lower()
        difficulty_examples = example_sets.get(difficulty.value, {})
        
        # Find matching examples
        for key in difficulty_examples:
            if key in concept_lower or concept_lower in key:
                return difficulty_examples[key]
        
        # Default examples if no match
        return difficulty_examples.get("general", ["real-world applications", "everyday examples", "practical uses"])
    
    def create_difficulty_selector_ui_data(self) -> Dict[str, Any]:
        """Return data for UI difficulty selector"""
        return {
            "levels": [
                {
                    "value": "kid",
                    "label": "👶 Kid Mode",
                    "description": "Simple explanations with fun examples",
                    "age_range": "8-12 years",
                    "style": "Stories and analogies"
                },
                {
                    "value": "teen", 
                    "label": "🧑 Teen Mode",
                    "description": "Clear explanations with relatable examples",
                    "age_range": "13-17 years",
                    "style": "Practical and engaging"
                },
                {
                    "value": "college",
                    "label": "🎓 College Mode", 
                    "description": "Technical depth with academic rigor",
                    "age_range": "18+ years",
                    "style": "Professional and comprehensive"
                }
            ],
            "default": "teen"
        }

# Example usage and testing
if __name__ == "__main__":
    # Example of how the adapter would work
    sample_content = "Atoms are the basic building blocks of matter."
    
    for difficulty in DifficultyLevel:
        print(f"\n{difficulty.value.upper()} LEVEL:")
        print("="*40)
        # This would use the actual AI engine in practice
        print(f"Adapted explanation would be generated here for {difficulty.value} level")
