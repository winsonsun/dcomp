import json
import math
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

class OntologyNode:
    def __init__(self, state: Dict[str, Any], parent=None, move: Dict[str, Any] = None):
        self.state = state  # The 'Graph' state
        self.parent = parent
        self.move = move    # The PDM directive that led to this state
        self.children: List['OntologyNode'] = []
        self.visits = 0
        self.value = 0.0
        self.is_terminal = False

    def uct_score(self, exploration_weight: float = 1.41) -> float:
        if self.visits == 0:
            return float('inf')
        return (self.value / self.visits) + exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)

class MCTSEngine:
    def __init__(self, evolver, initial_ontology: List[Dict[str, Any]], goal: str):
        self.evolver = evolver
        self.initial_ontology = initial_ontology
        self.goal = goal
        self.root = OntologyNode(state={"graph": initial_ontology, "plan": []})

    def run(self, iterations: int = 5) -> str:
        print(f"--- [MCTS] Beginning Search for Goal: '{self.goal}' ({iterations} iterations) ---")
        
        for i in range(iterations):
            print(f"  Iteration {i+1}...")
            # 1. Select
            node = self.select(self.root)
            
            # 2. Expand
            if not node.is_terminal:
                self.expand(node)
                if node.children:
                    node = random.choice(node.children)
            
            # 3. Simulate (Rollout)
            reward = self.simulate(node)
            
            # 4. Backpropagate
            self.backpropagate(node, reward)

        # Return the best plan found
        best_child = self.get_best_child(self.root)
        if best_child:
            return self.format_plan(best_child.state["plan"])
        return ""

    def select(self, node: OntologyNode) -> OntologyNode:
        while node.children:
            node = max(node.children, key=lambda c: c.uct_score())
        return node

    def expand(self, node: OntologyNode):
        """Calls LLM to propose next moves."""
        sys_prompt = "You are an architectural expansion engine. Propose 3-5 valid PDM JSONL directives to evolve the current system toward the goal."
        prompt = f"""
        Goal: {self.goal}
        Current Plan: {json.dumps(node.state['plan'])}
        Current Ontology: {json.dumps(node.state['graph'][:20])} (truncated)
        
        Output ONLY a JSON list of moves: [{{"op": "scaffold_noun", "target": "..."}}, ...]
        """
        
        response = self.evolver.run_llm(prompt, sys_prompt)
        try:
            # Clean JSON
            clean_json = response.replace('```json', '').replace('```', '').strip()
            moves = json.loads(clean_json)
            for move in moves:
                new_plan = node.state["plan"] + [move]
                # In a real system, we'd update the graph state here.
                new_state = {"graph": node.state["graph"], "plan": new_plan}
                child = OntologyNode(new_state, parent=node, move=move)
                node.children.append(child)
        except Exception as e:
            print(f"Warning: MCTS Expansion failed: {e}")

    def simulate(self, node: OntologyNode) -> float:
        """Calls fast LLM to score the current plan's fitness."""
        if not node.state["plan"]:
            return 0.0
            
        sys_prompt = "You are a senior architectural critic. Score this implementation plan on a scale of 0.0 to 1.0."
        prompt = f"""
        Goal: {self.goal}
        Proposed Plan: {json.dumps(node.state['plan'])}
        
        Score the plan's logic, safety, and architectural fit.
        Output ONLY a raw float number.
        """
        
        response = self.evolver.run_llm(prompt, sys_prompt)
        try:
            return float(response.strip())
        except:
            return 0.0

    def backpropagate(self, node: OntologyNode, reward: float):
        while node:
            node.visits += 1
            node.value += reward
            node = node.parent

    def get_best_child(self, node: OntologyNode) -> Optional[OntologyNode]:
        if not node.children:
            return None
        return max(node.children, key=lambda c: c.value / c.visits if c.visits > 0 else 0)

    def format_plan(self, plan: List[Dict[str, Any]]) -> str:
        return "\n".join(json.dumps(move) for move in plan)
