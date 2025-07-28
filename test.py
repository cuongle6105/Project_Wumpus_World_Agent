import random
from typing import Set, List, Tuple

class Rule:
    def __init__(self, premises: Set[str], conclusion: str):
        self.premises = premises
        self.conclusion = conclusion
    def triggered(self, facts: Set[str]) -> bool:
        return self.premises.issubset(facts)

class KnowledgeBase:
    def __init__(self):
        self.facts: Set[str] = set()
        self.neg_facts: Set[str] = set()
        self.rules: List[Rule] = []

    def add_fact(self, fact: str):
        if fact.startswith('-'):
            f = fact[1:]
            if f in self.facts:
                raise ValueError(f"Contradiction adding {fact}")
            self.neg_facts.add(f)
        else:
            if fact in self.neg_facts:
                raise ValueError(f"Contradiction adding {fact}")
            self.facts.add(fact)

    def add_rule(self, premises: List[str], conclusion: str):
        self.rules.append(Rule(set(premises), conclusion))

    def infer(self):
        changed = True
        while changed:
            changed = False
            remaining = []
            for r in self.rules:
                if r.triggered(self.facts):
                    if r.conclusion not in self.facts:
                        self.add_fact(r.conclusion)
                        changed = True
                else:
                    remaining.append(r)
            self.rules = remaining

class InferenceEngine:
    def __init__(self, world):
        self.world = world
        self.kb = KnowledgeBase()

    def infer(self, query: Tuple[int,int]) -> str:
        x, y = query
        percepts = self.world.set_agent(x, y)
        cell = f"{x}{y}"

        self.kb.add_fact(f"Safe{cell}")
        self.kb.add_fact(f"-W{cell}")
        self.kb.add_fact(f"-P{cell}")
        neigh = [f"{i}{j}" for i,j in self.world.adjacent(x,y)]

        if 'S' in percepts:
            self.kb.add_fact(f"S{cell}")
            for n in neigh:
                premises = [f"S{cell}"] + [f"-W{o}" for o in neigh if o != n]
                self.kb.add_rule(premises, f"W{n}")
        else:
            for n in neigh:
                self.kb.add_fact(f"-W{n}")
                
        # Breeze handling
        if 'B' in percepts:
            self.kb.add_fact(f"B{cell}")
            for n in neigh:
                premises = [f"B{cell}"] + [f"-P{o}" for o in neigh if o != n]
                self.kb.add_rule(premises, f"P{n}")
        else:
            for n in neigh:
                self.kb.add_fact(f"-P{n}")

        self.kb.infer()

        tag = f"{x}{y}"
        if f"W{tag}" in self.kb.facts or f"P{tag}" in self.kb.facts:
            return 'unsafe'

        for r in self.kb.rules:
            if r.conclusion in {f"W{tag}", f"P{tag}"} and r.premises and set(r.premises).issubset(self.kb.facts):
                return 'uncertain'
        return 'safe'
