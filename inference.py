import random

class Rule:
    def __init__(self, premises, conclusions):
        self.premises = set(premises)
        self.conclusions = set(conclusions)
    
    def triggered(self, facts):
        return self.premises.issubset(facts)
    
    
class KnowledgeBase:
    def __init__(self):
        self.facts = set() #unit facts
        self.neg_facts = set() #negative unit facts
        self.rules = [] #implications
        
    def addFact(self, fact):
        if (fact.startswith('-')):
            self.neg_facts.add(fact[1:])
        else:
            self.facts.add(fact)
    
    def addRule(self, rule):
        self.rules.append(rule)
        
    def removeFact(self, fact):
        if (fact.startswith('-')):
            self.neg_facts.discard(fact)
        else:
            self.facts.discard(fact[1:])
        
    def removeRule(self, rule):
        self.rules.remove(rule)
    
    
    def show(self):
        print("Facts:", self.facts)
        print("Negated:", self.neg_facts)
        print("Rules:", self.rules)

class InferenceEngine:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.uncertains = []
    
    def reset_wumpus_knowledge(self):
        # """ Removes all facts and rules related to Wumpus locations. """
        self.kb.facts = {f for f in self.kb.facts if not f.startswith('W')}
        self.kb.neg_facts = {f for f in self.kb.neg_facts if not f.startswith('W')}
        self.kb.rules = [r for r in self.kb.rules if not r.conclusion.startswith('W')]
    
    def infer(self, query):
        changed = True
        while changed:
            changed = False
            for rule in self.kb.rules:
                if (rule.triggered(self.kb.facts)):
                    self.uncertains.append(rule.conclusions)
                    self.kb.removeRule(rule)
                    changed = True
            
            still_uncertain = []
            for opts in self.uncertains:
                opts -= self.kb.facts 
                if len(opts) == 1:
                    fact = next(iter(opts))
                    if fact not in self.kb.facts:
                        self.kb.addFact(fact)
                        changed = True
                else:
                    still_uncertain.append(opts)
            self.uncertains = still_uncertain
            
            is_unsafe = False
            is_uncertain = False
            xpos = query[0]
            ypos = query[1]
            
            name = lambda i, j: f"{i}{j}"
            
            dangerous_facts = {f"W{name(xpos, ypos)}", f"P{name(xpos, ypos)}"}
            
            for fact in dangerous_facts:
                if fact in self.kb.facts:
                    is_unsafe = True
                    break 
                
            if not is_unsafe:
                for opts in self.uncertains:
                    if (f"W{name(xpos, ypos)}" in opts) or \
                    (f"P{name(xpos, ypos)}" in opts):
                        is_uncertain = True
                        break

            if is_unsafe:
                return "unsafe"
            elif is_uncertain:
                return "uncertain"
            else:
                return "safe"
    
    def process_percepts(self, x, y, percepts, world):
        name = lambda i, j: f"{i}{j}"
        self.kb.addFact(f"Safe{name(x, y)}")
        self.kb.addFact(f"-W{x}{y}")
        self.kb.addFact(f"-P{x}{y}")
        
        if 'S' in percepts:
            options = [f"W{name(i,j)}" for i,j in world.adjacent(x, y)]
            self.kb.addRule(Rule(premises=[f"S{name(x,y)}"], conclusions=options))
            self.kb.addFact(f"S{name(x,y)}")

        if 'B' in percepts:
            options = [f"P{name(i,j)}" for i,j in world.adjacent(x, y)]
            self.kb.addRule(Rule(premises=[f"B{name(x,y)}"], conclusions=options))
            self.kb.addFact(f"B{name(x,y)}")
        
        if 'S' not in percepts and 'B' not in percepts:
            self.kb.addFact(f"-W{x}{y}")
            self.kb.addFact(f"-P{x}{y}")
            self.kb.addFact(f"Safe{x}{y}")
            for i, j in world.adjacent(x, y):
                self.kb.addFact(f"-W{i}{j}")
                self.kb.addFact(f"-P{i}{j}")
                self.kb.addFact(f"Safe{i}{j}")
                
    def printUncertains(self):
        print("uncertain:", self.uncertains)