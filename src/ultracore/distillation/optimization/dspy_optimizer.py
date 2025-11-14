"""DSPy-based Prompt Optimization"""
from typing import List, Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class DSPyOptimizer:
    """
    DSPy-inspired prompt optimization through example search.
    
    DSPy searches for existing examples that improve prompt performance
    through bootstrap learning and teleprompter algorithms.
    """
    
    def __init__(self, teacher_model: str = "gpt-4"):
        self.teacher_model = teacher_model
        self.prompt_history: List[Dict[str, Any]] = []
        logger.info("DSPyOptimizer initialized")
    
    async def optimize(
        self,
        initial_prompt: str,
        training_examples: List[Dict[str, Any]],
        evaluation_function: Callable,
        iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize prompt using DSPy-style bootstrap learning.
        
        Args:
            initial_prompt: Starting prompt template
            training_examples: Training data
            evaluation_function: Function to evaluate prompt performance
            iterations: Number of optimization iterations
        
        Returns:
            Dict with optimized_prompt and metrics
        """
        logger.info(f"Starting DSPy optimization for {iterations} iterations")
        
        current_prompt = initial_prompt
        best_prompt = initial_prompt
        best_score = 0.0
        
        for iteration in range(iterations):
            logger.debug(f"DSPy iteration {iteration + 1}/{iterations}")
            
            # Bootstrap: Generate few-shot examples
            few_shot_examples = await self._bootstrap_examples(
                training_examples,
                n_examples=5
            )
            
            # Create prompt with few-shot examples
            enhanced_prompt = self._add_few_shot(current_prompt, few_shot_examples)
            
            # Evaluate
            score = await evaluation_function(enhanced_prompt, training_examples)
            
            logger.debug(f"Iteration {iteration + 1} score: {score:.3f}")
            
            # Track history
            self.prompt_history.append({
                "iteration": iteration + 1,
                "prompt": enhanced_prompt,
                "score": score,
                "method": "dspy"
            })
            
            # Update best
            if score > best_score:
                best_score = score
                best_prompt = enhanced_prompt
                logger.info(f"New best score: {best_score:.3f}")
            
            # Update current prompt for next iteration
            current_prompt = best_prompt
        
        result = {
            "optimized_prompt": best_prompt,
            "initial_score": self.prompt_history[0]["score"] if self.prompt_history else 0.0,
            "final_score": best_score,
            "improvement": best_score - (self.prompt_history[0]["score"] if self.prompt_history else 0.0),
            "iterations": iterations,
            "method": "dspy"
        }
        
        logger.info(
            f"DSPy optimization complete: "
            f"{result['initial_score']:.1%} → {result['final_score']:.1%} "
            f"(+{result['improvement']:.1%})"
        )
        
        return result
    
    async def _bootstrap_examples(
        self,
        training_examples: List[Dict[str, Any]],
        n_examples: int = 5
    ) -> List[Dict[str, Any]]:
        """Bootstrap representative examples for few-shot learning."""
        
        # Select diverse, high-quality examples
        # Prioritize:
        # 1. High teacher confidence
        # 2. Successful outcomes
        # 3. Diverse tool selections
        
        scored_examples = []
        for ex in training_examples:
            score = 0.0
            
            # Teacher confidence
            score += ex.get("teacher_confidence", 0.0) * 0.5
            
            # Success
            if ex.get("outcome", {}).get("success"):
                score += 0.3
            
            # Reasoning quality (length as proxy)
            reasoning_length = len(ex.get("reasoning", ""))
            score += min(reasoning_length / 200, 0.2)
            
            scored_examples.append((score, ex))
        
        # Sort by score and select top N
        scored_examples.sort(reverse=True, key=lambda x: x[0])
        selected = [ex for _, ex in scored_examples[:n_examples]]
        
        logger.debug(f"Bootstrapped {len(selected)} examples")
        return selected
    
    def _add_few_shot(
        self,
        prompt: str,
        examples: List[Dict[str, Any]]
    ) -> str:
        """Add few-shot examples to prompt."""
        
        if not examples:
            return prompt
        
        few_shot_text = "\n\nHere are some examples:\n\n"
        
        for i, ex in enumerate(examples, 1):
            few_shot_text += f"Example {i}:\n"
            few_shot_text += f"Context: {ex.get('context', {})}\n"
            few_shot_text += f"Available tools: {[t['name'] for t in ex.get('tools_available', [])]}\n"
            few_shot_text += f"Selected: {ex.get('tool_selected')}\n"
            few_shot_text += f"Reasoning: {ex.get('reasoning')}\n\n"
        
        return prompt + few_shot_text
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return self.prompt_history.copy()
