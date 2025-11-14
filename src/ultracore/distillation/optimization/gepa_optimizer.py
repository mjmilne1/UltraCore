"""GEPA (Generative Evolutionary Prompt Adaptation) Optimizer"""
from typing import List, Dict, Any, Callable, Optional
import random
import logging

logger = logging.getLogger(__name__)


class GEPAOptimizer:
    """
    GEPA-style prompt optimization through evolutionary search.
    
    GEPA uses multi-objective evolutionary algorithms with natural language
    feedback to evolve prompts toward better performance.
    """
    
    def __init__(self, teacher_model: str = "gpt-4"):
        self.teacher_model = teacher_model
        self.population_size = 5
        self.mutation_rate = 0.3
        self.prompt_history: List[Dict[str, Any]] = []
        logger.info("GEPAOptimizer initialized")
    
    async def optimize(
        self,
        initial_prompt: str,
        training_examples: List[Dict[str, Any]],
        evaluation_function: Callable,
        generations: int = 10
    ) -> Dict[str, Any]:
        """
        Optimize prompt using GEPA-style evolutionary search.
        
        Args:
            initial_prompt: Starting prompt
            training_examples: Training data
            evaluation_function: Function to evaluate prompt performance
            generations: Number of evolutionary generations
        
        Returns:
            Dict with optimized_prompt and metrics
        """
        logger.info(f"Starting GEPA optimization for {generations} generations")
        
        # Initialize population
        population = await self._initialize_population(initial_prompt)
        
        best_prompt = initial_prompt
        best_score = 0.0
        
        for generation in range(generations):
            logger.debug(f"GEPA generation {generation + 1}/{generations}")
            
            # Evaluate population
            fitness_scores = []
            for prompt in population:
                score = await evaluation_function(prompt, training_examples)
                fitness_scores.append(score)
            
            # Track best
            gen_best_idx = fitness_scores.index(max(fitness_scores))
            gen_best_score = fitness_scores[gen_best_idx]
            
            if gen_best_score > best_score:
                best_score = gen_best_score
                best_prompt = population[gen_best_idx]
                logger.info(f"Generation {generation + 1} new best: {best_score:.3f}")
            
            # Track history
            self.prompt_history.append({
                "generation": generation + 1,
                "best_prompt": population[gen_best_idx],
                "best_score": gen_best_score,
                "avg_score": sum(fitness_scores) / len(fitness_scores),
                "method": "gepa"
            })
            
            # Selection
            selected = self._select(population, fitness_scores)
            
            # Crossover
            offspring = await self._crossover(selected)
            
            # Mutation
            mutated = await self._mutate(offspring, training_examples)
            
            # New population
            population = mutated
        
        result = {
            "optimized_prompt": best_prompt,
            "initial_score": self.prompt_history[0]["best_score"] if self.prompt_history else 0.0,
            "final_score": best_score,
            "improvement": best_score - (self.prompt_history[0]["best_score"] if self.prompt_history else 0.0),
            "generations": generations,
            "method": "gepa"
        }
        
        logger.info(
            f"GEPA optimization complete: "
            f"{result['initial_score']:.1%} → {result['final_score']:.1%} "
            f"(+{result['improvement']:.1%})"
        )
        
        return result
    
    async def _initialize_population(self, initial_prompt: str) -> List[str]:
        """Initialize population with variations of initial prompt."""
        
        population = [initial_prompt]
        
        # Create variations
        variations = [
            initial_prompt + "\n\nBe concise and precise.",
            initial_prompt + "\n\nConsider all available context.",
            initial_prompt + "\n\nExplain your reasoning step by step.",
            initial_prompt + "\n\nPrioritize accuracy over speed."
        ]
        
        population.extend(variations[:self.population_size - 1])
        
        logger.debug(f"Initialized population of {len(population)}")
        return population
    
    def _select(
        self,
        population: List[str],
        fitness_scores: List[float]
    ) -> List[str]:
        """Select prompts for next generation (tournament selection)."""
        
        selected = []
        
        for _ in range(self.population_size):
            # Tournament selection
            tournament_size = 3
            tournament_indices = random.sample(range(len(population)), tournament_size)
            tournament_scores = [fitness_scores[i] for i in tournament_indices]
            winner_idx = tournament_indices[tournament_scores.index(max(tournament_scores))]
            selected.append(population[winner_idx])
        
        return selected
    
    async def _crossover(self, selected: List[str]) -> List[str]:
        """Crossover selected prompts."""
        
        offspring = []
        
        for i in range(0, len(selected) - 1, 2):
            parent1 = selected[i]
            parent2 = selected[i + 1]
            
            # Simple crossover: combine parts of both prompts
            lines1 = parent1.split('\n')
            lines2 = parent2.split('\n')
            
            # Take first half from parent1, second half from parent2
            mid1 = len(lines1) // 2
            mid2 = len(lines2) // 2
            
            child1 = '\n'.join(lines1[:mid1] + lines2[mid2:])
            child2 = '\n'.join(lines2[:mid2] + lines1[mid1:])
            
            offspring.extend([child1, child2])
        
        # Add remaining
        if len(selected) % 2 == 1:
            offspring.append(selected[-1])
        
        return offspring[:self.population_size]
    
    async def _mutate(
        self,
        offspring: List[str],
        training_examples: List[Dict[str, Any]]
    ) -> List[str]:
        """Mutate prompts with natural language feedback."""
        
        mutated = []
        
        for prompt in offspring:
            if random.random() < self.mutation_rate:
                # Apply mutation
                mutation_type = random.choice([
                    "add_emphasis",
                    "add_constraint",
                    "add_example",
                    "simplify"
                ])
                
                if mutation_type == "add_emphasis":
                    prompt += "\n\nThis is critical for accuracy."
                elif mutation_type == "add_constraint":
                    prompt += "\n\nAlways verify your selection."
                elif mutation_type == "add_example":
                    if training_examples:
                        ex = random.choice(training_examples)
                        prompt += f"\n\nFor example: {ex.get('reasoning', '')}"
                elif mutation_type == "simplify":
                    # Remove last line
                    lines = prompt.split('\n')
                    prompt = '\n'.join(lines[:-1]) if len(lines) > 1 else prompt
            
            mutated.append(prompt)
        
        return mutated
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return self.prompt_history.copy()


class CombinedOptimizer:
    """Combines DSPy and GEPA for maximum improvement."""
    
    def __init__(self, teacher_model: str = "gpt-4"):
        self.dspy = DSPyOptimizer(teacher_model)
        self.gepa = GEPAOptimizer(teacher_model)
        logger.info("CombinedOptimizer initialized")
    
    async def optimize(
        self,
        initial_prompt: str,
        training_examples: List[Dict[str, Any]],
        evaluation_function: Callable
    ) -> Dict[str, Any]:
        """
        Optimize using DSPy first, then GEPA.
        
        This mirrors the article's approach: DSPy improves from 0% to 12%,
        then GEPA pushes to 93%.
        """
        logger.info("Starting combined optimization (DSPy → GEPA)")
        
        # Phase 1: DSPy
        dspy_result = await self.dspy.optimize(
            initial_prompt,
            training_examples,
            evaluation_function,
            iterations=5
        )
        
        # Phase 2: GEPA (starting from DSPy result)
        gepa_result = await self.gepa.optimize(
            dspy_result["optimized_prompt"],
            training_examples,
            evaluation_function,
            generations=10
        )
        
        result = {
            "optimized_prompt": gepa_result["optimized_prompt"],
            "initial_score": dspy_result["initial_score"],
            "dspy_score": dspy_result["final_score"],
            "final_score": gepa_result["final_score"],
            "dspy_improvement": dspy_result["improvement"],
            "gepa_improvement": gepa_result["improvement"],
            "total_improvement": gepa_result["final_score"] - dspy_result["initial_score"],
            "method": "combined"
        }
        
        logger.info(
            f"Combined optimization complete:\n"
            f"  Initial: {result['initial_score']:.1%}\n"
            f"  After DSPy: {result['dspy_score']:.1%} (+{result['dspy_improvement']:.1%})\n"
            f"  After GEPA: {result['final_score']:.1%} (+{result['gepa_improvement']:.1%})\n"
            f"  Total: +{result['total_improvement']:.1%}"
        )
        
        return result
