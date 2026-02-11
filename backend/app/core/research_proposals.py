"""
Research Proposal Generator
Transforms high-novelty insights into actionable research proposals.

This system takes breakthrough insights from the meta-intelligence
and generates structured research proposals with hypotheses,
methodologies, resources, and expected outcomes.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re


class ProposalStatus(Enum):
    """Status of a research proposal"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResearchPhase(Enum):
    """Phases of research"""
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_FORMATION = "hypothesis_formation"
    METHODOLOGY_DESIGN = "methodology_design"
    EXPERIMENTATION = "experimentation"
    DATA_ANALYSIS = "data_analysis"
    CONCLUSION = "conclusion"
    PUBLICATION = "publication"


@dataclass
class ResearchMilestone:
    """A milestone in the research timeline"""
    name: str
    phase: ResearchPhase
    description: str
    estimated_weeks: int
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)


@dataclass
class ResearchResource:
    """A resource needed for research"""
    category: str  # "equipment", "personnel", "funding", "data", "software"
    name: str
    description: str
    estimated_cost: Optional[float] = None
    availability: str = "available"  # "available", "needs_procurement", "needs_development"


@dataclass
class ResearchProposal:
    """A complete research proposal"""
    id: str
    title: str
    abstract: str
    source_insight_id: str
    source_insight_content: str
    
    # Core components
    hypothesis: str
    null_hypothesis: str
    research_questions: List[str]
    objectives: List[str]
    
    # Methodology
    methodology: Dict[str, Any]
    experimental_design: str
    variables: Dict[str, List[str]]  # "independent", "dependent", "controlled"
    
    # Timeline and resources
    milestones: List[ResearchMilestone]
    resources: List[ResearchResource]
    estimated_duration_weeks: int
    estimated_budget: float
    
    # Expected outcomes
    expected_outcomes: List[str]
    potential_impact: str
    success_metrics: List[str]
    risk_assessment: List[Dict[str, str]]
    
    # Metadata
    domains: List[str]
    keywords: List[str]
    novelty_score: float
    testability_score: float
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "abstract": self.abstract,
            "source_insight_id": self.source_insight_id,
            "source_insight_content": self.source_insight_content,
            "hypothesis": self.hypothesis,
            "null_hypothesis": self.null_hypothesis,
            "research_questions": self.research_questions,
            "objectives": self.objectives,
            "methodology": self.methodology,
            "experimental_design": self.experimental_design,
            "variables": self.variables,
            "milestones": [
                {
                    "name": m.name,
                    "phase": m.phase.value,
                    "description": m.description,
                    "estimated_weeks": m.estimated_weeks,
                    "dependencies": m.dependencies,
                    "deliverables": m.deliverables
                }
                for m in self.milestones
            ],
            "resources": [
                {
                    "category": r.category,
                    "name": r.name,
                    "description": r.description,
                    "estimated_cost": r.estimated_cost,
                    "availability": r.availability
                }
                for r in self.resources
            ],
            "estimated_duration_weeks": self.estimated_duration_weeks,
            "estimated_budget": self.estimated_budget,
            "expected_outcomes": self.expected_outcomes,
            "potential_impact": self.potential_impact,
            "success_metrics": self.success_metrics,
            "risk_assessment": self.risk_assessment,
            "domains": self.domains,
            "keywords": self.keywords,
            "novelty_score": self.novelty_score,
            "testability_score": self.testability_score,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ResearchProposalGenerator:
    """
    Generates research proposals from insights.
    
    Takes high-novelty insights and transforms them into structured,
    actionable research proposals with all necessary components.
    """
    
    def __init__(self):
        self.proposals: Dict[str, ResearchProposal] = {}
        self.proposal_counter = 0
        
        # Templates for different research domains
        self.domain_methodologies = {
            "physics": {
                "approach": "experimental_theoretical",
                "methods": ["simulation", "mathematical_modeling", "laboratory_experiment"],
                "typical_phases": [
                    ResearchPhase.LITERATURE_REVIEW,
                    ResearchPhase.HYPOTHESIS_FORMATION,
                    ResearchPhase.METHODOLOGY_DESIGN,
                    ResearchPhase.EXPERIMENTATION,
                    ResearchPhase.DATA_ANALYSIS,
                    ResearchPhase.CONCLUSION
                ]
            },
            "biology": {
                "approach": "experimental",
                "methods": ["in_vitro", "in_vivo", "computational_biology", "sequencing"],
                "typical_phases": [
                    ResearchPhase.LITERATURE_REVIEW,
                    ResearchPhase.HYPOTHESIS_FORMATION,
                    ResearchPhase.METHODOLOGY_DESIGN,
                    ResearchPhase.EXPERIMENTATION,
                    ResearchPhase.DATA_ANALYSIS,
                    ResearchPhase.CONCLUSION
                ]
            },
            "ai": {
                "approach": "computational",
                "methods": ["machine_learning", "deep_learning", "reinforcement_learning", "ablation_study"],
                "typical_phases": [
                    ResearchPhase.LITERATURE_REVIEW,
                    ResearchPhase.HYPOTHESIS_FORMATION,
                    ResearchPhase.METHODOLOGY_DESIGN,
                    ResearchPhase.EXPERIMENTATION,
                    ResearchPhase.DATA_ANALYSIS,
                    ResearchPhase.CONCLUSION,
                    ResearchPhase.PUBLICATION
                ]
            },
            "neuroscience": {
                "approach": "experimental_computational",
                "methods": ["imaging", "electrophysiology", "behavioral", "computational_modeling"],
                "typical_phases": [
                    ResearchPhase.LITERATURE_REVIEW,
                    ResearchPhase.HYPOTHESIS_FORMATION,
                    ResearchPhase.METHODOLOGY_DESIGN,
                    ResearchPhase.EXPERIMENTATION,
                    ResearchPhase.DATA_ANALYSIS,
                    ResearchPhase.CONCLUSION
                ]
            },
            "technology": {
                "approach": "engineering",
                "methods": ["prototyping", "testing", "iteration", "validation"],
                "typical_phases": [
                    ResearchPhase.LITERATURE_REVIEW,
                    ResearchPhase.METHODOLOGY_DESIGN,
                    ResearchPhase.EXPERIMENTATION,
                    ResearchPhase.DATA_ANALYSIS,
                    ResearchPhase.CONCLUSION
                ]
            }
        }
        
        # Resource templates
        self.resource_templates = {
            "computational": [
                ResearchResource("equipment", "High-performance computing cluster", "For simulations and model training", 50000, "available"),
                ResearchResource("software", "Research software licenses", "MATLAB, specialized simulation tools", 5000, "available"),
                ResearchResource("data", "Training/validation datasets", "Curated datasets for experiments", 0, "needs_procurement"),
            ],
            "experimental": [
                ResearchResource("equipment", "Laboratory equipment", "Specialized experimental apparatus", 100000, "needs_procurement"),
                ResearchResource("personnel", "Research assistants", "Graduate students or postdocs", 80000, "needs_procurement"),
                ResearchResource("equipment", "Measurement instruments", "High-precision sensors and meters", 30000, "available"),
            ],
            "theoretical": [
                ResearchResource("software", "Mathematical software", "Mathematica, symbolic computation tools", 3000, "available"),
                ResearchResource("personnel", "Research collaborators", "Domain experts for consultation", 20000, "available"),
            ]
        }
    
    def generate_proposal(
        self,
        insight_id: str,
        insight_content: str,
        domains: List[str],
        novelty_score: float,
        testability_score: float,
        key_concepts: List[str] = None
    ) -> ResearchProposal:
        """
        Generate a research proposal from an insight.
        
        Args:
            insight_id: ID of the source insight
            insight_content: Content of the insight
            domains: Scientific domains the insight touches
            novelty_score: How novel the insight is (0-1)
            testability_score: How testable the insight is (0-1)
            key_concepts: Key concepts extracted from the insight
            
        Returns:
            A complete ResearchProposal
        """
        self.proposal_counter += 1
        proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d')}-{self.proposal_counter:04d}"
        
        # Generate components
        title = self._generate_title(insight_content, domains)
        abstract = self._generate_abstract(insight_content, domains, novelty_score)
        hypothesis, null_hypothesis = self._generate_hypotheses(insight_content)
        research_questions = self._generate_research_questions(insight_content, domains)
        objectives = self._generate_objectives(insight_content, research_questions)
        
        # Determine methodology based on domains
        primary_domain = domains[0] if domains else "technology"
        methodology = self._generate_methodology(primary_domain, insight_content)
        experimental_design = self._generate_experimental_design(primary_domain, hypothesis)
        variables = self._generate_variables(insight_content, key_concepts or [])
        
        # Generate timeline and resources
        milestones = self._generate_milestones(primary_domain, novelty_score)
        resources = self._generate_resources(primary_domain, methodology)
        
        duration = sum(m.estimated_weeks for m in milestones)
        budget = sum(r.estimated_cost or 0 for r in resources)
        
        # Generate outcomes and metrics
        expected_outcomes = self._generate_expected_outcomes(insight_content, hypothesis)
        potential_impact = self._generate_impact_statement(insight_content, domains, novelty_score)
        success_metrics = self._generate_success_metrics(research_questions, expected_outcomes)
        risk_assessment = self._generate_risk_assessment(novelty_score, testability_score)
        
        # Extract keywords
        keywords = self._extract_keywords(insight_content, key_concepts or [])
        
        proposal = ResearchProposal(
            id=proposal_id,
            title=title,
            abstract=abstract,
            source_insight_id=insight_id,
            source_insight_content=insight_content,
            hypothesis=hypothesis,
            null_hypothesis=null_hypothesis,
            research_questions=research_questions,
            objectives=objectives,
            methodology=methodology,
            experimental_design=experimental_design,
            variables=variables,
            milestones=milestones,
            resources=resources,
            estimated_duration_weeks=duration,
            estimated_budget=budget,
            expected_outcomes=expected_outcomes,
            potential_impact=potential_impact,
            success_metrics=success_metrics,
            risk_assessment=risk_assessment,
            domains=domains,
            keywords=keywords,
            novelty_score=novelty_score,
            testability_score=testability_score
        )
        
        self.proposals[proposal_id] = proposal
        return proposal
    
    def _generate_title(self, content: str, domains: List[str]) -> str:
        """Generate a research title"""
        # Extract key phrases
        words = content.split()[:20]
        key_phrase = " ".join(words)
        
        # Clean and format
        domain_str = " and ".join(domains[:2]) if domains else "Interdisciplinary"
        
        # Create title
        if "connection" in content.lower() or "link" in content.lower():
            return f"Investigating Cross-Domain Connections: {key_phrase[:60]}..."
        elif "novel" in content.lower() or "new" in content.lower():
            return f"A Novel Approach to {domain_str.title()}: {key_phrase[:50]}..."
        else:
            return f"Exploring {domain_str.title()} Insights: {key_phrase[:50]}..."
    
    def _generate_abstract(self, content: str, domains: List[str], novelty: float) -> str:
        """Generate research abstract"""
        novelty_desc = "highly novel" if novelty > 0.7 else "promising" if novelty > 0.4 else "exploratory"
        domain_str = ", ".join(domains) if domains else "interdisciplinary research"
        
        return f"""This research proposal investigates a {novelty_desc} insight emerging from {domain_str}. 
The central observation is: {content[:200]}...

This proposal outlines a systematic approach to validate, extend, and apply this insight through 
rigorous experimental and theoretical methodology. We aim to establish empirical evidence for 
the proposed relationships and explore potential applications."""
    
    def _generate_hypotheses(self, content: str) -> tuple:
        """Generate hypothesis and null hypothesis"""
        # Extract the core claim
        content_lower = content.lower()
        
        if "connection" in content_lower:
            hypothesis = f"There exists a significant relationship between the concepts described: {content[:100]}..."
            null_hypothesis = "No significant relationship exists between the concepts described."
        elif "effect" in content_lower or "impact" in content_lower:
            hypothesis = f"The proposed effect is measurable and reproducible: {content[:100]}..."
            null_hypothesis = "The proposed effect is not measurable or is due to random variation."
        else:
            hypothesis = f"The insight described is valid and can be empirically demonstrated: {content[:100]}..."
            null_hypothesis = "The insight cannot be empirically supported and represents coincidence or error."
        
        return hypothesis, null_hypothesis
    
    def _generate_research_questions(self, content: str, domains: List[str]) -> List[str]:
        """Generate research questions"""
        questions = [
            f"What is the mechanism underlying the observed relationship?",
            f"Under what conditions does this insight hold true?",
            f"What are the boundary conditions and limitations?",
        ]
        
        if len(domains) > 1:
            questions.append(f"How do the domains of {' and '.join(domains[:2])} interact in this context?")
        
        if "novel" in content.lower() or "new" in content.lower():
            questions.append("How does this insight compare to existing knowledge in the field?")
        
        return questions
    
    def _generate_objectives(self, content: str, questions: List[str]) -> List[str]:
        """Generate research objectives"""
        objectives = [
            "Validate the core insight through empirical investigation",
            "Identify and characterize the underlying mechanisms",
            "Establish reproducibility and reliability of findings",
            "Explore practical applications and implications",
        ]
        
        # Add question-specific objectives
        for i, q in enumerate(questions[:2]):
            objectives.append(f"Address research question {i+1}: {q[:50]}...")
        
        return objectives
    
    def _generate_methodology(self, domain: str, content: str) -> Dict[str, Any]:
        """Generate methodology based on domain"""
        template = self.domain_methodologies.get(domain, self.domain_methodologies["technology"])
        
        return {
            "approach": template["approach"],
            "methods": template["methods"],
            "data_collection": self._suggest_data_collection(domain, content),
            "analysis_techniques": self._suggest_analysis_techniques(domain),
            "validation_approach": "Cross-validation with multiple independent methods"
        }
    
    def _suggest_data_collection(self, domain: str, content: str) -> List[str]:
        """Suggest data collection methods"""
        suggestions = {
            "physics": ["Sensor measurements", "Simulation outputs", "Mathematical derivations"],
            "biology": ["Laboratory assays", "Imaging data", "Genomic/proteomic data"],
            "ai": ["Benchmark datasets", "Generated synthetic data", "Real-world test cases"],
            "neuroscience": ["Brain imaging", "Behavioral measurements", "Electrophysiology"],
            "technology": ["User studies", "Performance benchmarks", "Prototype testing"]
        }
        return suggestions.get(domain, ["Observational data", "Experimental measurements"])
    
    def _suggest_analysis_techniques(self, domain: str) -> List[str]:
        """Suggest analysis techniques"""
        suggestions = {
            "physics": ["Statistical analysis", "Numerical simulation", "Error propagation"],
            "biology": ["Statistical testing", "Bioinformatics", "Visualization"],
            "ai": ["Model evaluation metrics", "Ablation studies", "Statistical significance testing"],
            "neuroscience": ["Signal processing", "Statistical parametric mapping", "Connectivity analysis"],
            "technology": ["Performance metrics", "User experience analysis", "Comparative evaluation"]
        }
        return suggestions.get(domain, ["Statistical analysis", "Qualitative assessment"])
    
    def _generate_experimental_design(self, domain: str, hypothesis: str) -> str:
        """Generate experimental design description"""
        return f"""
Experimental Design for {domain.title()} Research:

1. Control Group: Baseline conditions without the proposed intervention/relationship
2. Experimental Group: Conditions implementing the insight
3. Randomization: Random assignment where applicable
4. Blinding: Double-blind where possible to reduce bias
5. Replication: Minimum 3 independent replications
6. Sample Size: Determined by power analysis for statistical significance

The design aims to test: {hypothesis[:100]}...
"""
    
    def _generate_variables(self, content: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Generate variable definitions"""
        # Use concepts as basis for variables
        independent = concepts[:2] if len(concepts) >= 2 else ["Primary manipulation variable"]
        dependent = concepts[2:4] if len(concepts) >= 4 else ["Outcome measure"]
        controlled = ["Environmental conditions", "Measurement protocols", "Sample characteristics"]
        
        return {
            "independent": independent,
            "dependent": dependent,
            "controlled": controlled
        }
    
    def _generate_milestones(self, domain: str, novelty: float) -> List[ResearchMilestone]:
        """Generate research milestones"""
        template = self.domain_methodologies.get(domain, self.domain_methodologies["technology"])
        
        # Adjust duration based on novelty (higher novelty = more time needed)
        duration_multiplier = 1.0 + (novelty * 0.5)
        
        milestones = []
        
        phase_details = {
            ResearchPhase.LITERATURE_REVIEW: {
                "name": "Literature Review and Background",
                "description": "Comprehensive review of existing research and establish theoretical framework",
                "base_weeks": 4,
                "deliverables": ["Literature review document", "Theoretical framework", "Research gaps identified"]
            },
            ResearchPhase.HYPOTHESIS_FORMATION: {
                "name": "Hypothesis Refinement",
                "description": "Refine hypotheses based on literature and develop testable predictions",
                "base_weeks": 2,
                "deliverables": ["Refined hypotheses", "Testable predictions", "Experimental plan"]
            },
            ResearchPhase.METHODOLOGY_DESIGN: {
                "name": "Methodology Design",
                "description": "Design experimental protocols and prepare materials/equipment",
                "base_weeks": 4,
                "deliverables": ["Detailed protocols", "Equipment setup", "Pilot study results"]
            },
            ResearchPhase.EXPERIMENTATION: {
                "name": "Data Collection",
                "description": "Execute experiments and collect data according to protocols",
                "base_weeks": 8,
                "deliverables": ["Raw data", "Experimental logs", "Initial observations"]
            },
            ResearchPhase.DATA_ANALYSIS: {
                "name": "Data Analysis",
                "description": "Analyze collected data using planned statistical methods",
                "base_weeks": 4,
                "deliverables": ["Statistical analysis", "Visualizations", "Results interpretation"]
            },
            ResearchPhase.CONCLUSION: {
                "name": "Conclusions and Reporting",
                "description": "Draw conclusions, write reports, and prepare for dissemination",
                "base_weeks": 4,
                "deliverables": ["Final report", "Conclusions document", "Future directions"]
            },
            ResearchPhase.PUBLICATION: {
                "name": "Publication Preparation",
                "description": "Prepare manuscripts for peer-reviewed publication",
                "base_weeks": 6,
                "deliverables": ["Manuscript draft", "Supplementary materials", "Submission package"]
            }
        }
        
        previous_milestone = None
        for phase in template["typical_phases"]:
            details = phase_details[phase]
            weeks = int(details["base_weeks"] * duration_multiplier)
            
            milestone = ResearchMilestone(
                name=details["name"],
                phase=phase,
                description=details["description"],
                estimated_weeks=weeks,
                dependencies=[previous_milestone] if previous_milestone else [],
                deliverables=details["deliverables"]
            )
            milestones.append(milestone)
            previous_milestone = details["name"]
        
        return milestones
    
    def _generate_resources(self, domain: str, methodology: Dict) -> List[ResearchResource]:
        """Generate resource requirements"""
        resources = []
        
        # Add based on approach
        approach = methodology.get("approach", "computational")
        if "computational" in approach:
            resources.extend(self.resource_templates["computational"])
        if "experimental" in approach:
            resources.extend(self.resource_templates["experimental"])
        if "theoretical" in approach:
            resources.extend(self.resource_templates["theoretical"])
        
        # Add basic resources
        resources.append(ResearchResource(
            "personnel", "Principal Investigator time", 
            "Time allocation for project lead", 0, "available"
        ))
        
        return resources
    
    def _generate_expected_outcomes(self, content: str, hypothesis: str) -> List[str]:
        """Generate expected outcomes"""
        return [
            "Empirical validation or refutation of the proposed hypothesis",
            "Quantitative characterization of the observed relationships",
            "New theoretical understanding contributing to the field",
            "Potential applications identified and evaluated",
            "Publication of findings in peer-reviewed venues",
            "Dataset and materials made available for reproducibility"
        ]
    
    def _generate_impact_statement(self, content: str, domains: List[str], novelty: float) -> str:
        """Generate potential impact statement"""
        domain_str = " and ".join(domains) if domains else "science"
        impact_level = "transformative" if novelty > 0.8 else "significant" if novelty > 0.5 else "meaningful"
        
        return f"""This research has {impact_level} potential impact on {domain_str}. 
If validated, the findings could advance our understanding of {content[:50]}... 
and open new avenues for research and practical applications. The cross-domain 
nature of this insight suggests potential for broad interdisciplinary impact."""
    
    def _generate_success_metrics(self, questions: List[str], outcomes: List[str]) -> List[str]:
        """Generate success metrics"""
        return [
            "Statistical significance achieved (p < 0.05) for primary hypotheses",
            "Effect size meeting practical significance thresholds",
            "Successful replication across independent experiments",
            "Peer review acceptance for publication",
            f"All {len(questions)} research questions addressed",
            "Clear conclusions regarding hypothesis validity"
        ]
    
    def _generate_risk_assessment(self, novelty: float, testability: float) -> List[Dict[str, str]]:
        """Generate risk assessment"""
        risks = []
        
        if novelty > 0.7:
            risks.append({
                "risk": "High novelty may lead to unexpected challenges",
                "mitigation": "Build in contingency time and alternative approaches",
                "severity": "medium"
            })
        
        if testability < 0.5:
            risks.append({
                "risk": "Low testability may limit empirical validation",
                "mitigation": "Develop proxy measures and indirect validation methods",
                "severity": "high"
            })
        
        risks.extend([
            {
                "risk": "Technical difficulties with equipment or methods",
                "mitigation": "Pilot testing and backup equipment",
                "severity": "medium"
            },
            {
                "risk": "Null results leading to inconclusive findings",
                "mitigation": "Pre-registration and commitment to publish null results",
                "severity": "low"
            },
            {
                "risk": "Timeline delays",
                "mitigation": "Regular progress reviews and buffer time",
                "severity": "medium"
            }
        ])
        
        return risks
    
    def _extract_keywords(self, content: str, concepts: List[str]) -> List[str]:
        """Extract keywords from content"""
        # Start with concepts
        keywords = list(concepts[:5])
        
        # Add common research terms found in content
        research_terms = ["novel", "mechanism", "relationship", "connection", "system", 
                         "model", "theory", "hypothesis", "experiment", "analysis"]
        
        content_lower = content.lower()
        for term in research_terms:
            if term in content_lower and term not in keywords:
                keywords.append(term)
        
        return keywords[:10]
    
    def get_proposal(self, proposal_id: str) -> Optional[ResearchProposal]:
        """Get a proposal by ID"""
        return self.proposals.get(proposal_id)
    
    def list_proposals(self, status: ProposalStatus = None) -> List[Dict[str, Any]]:
        """List all proposals, optionally filtered by status"""
        proposals = self.proposals.values()
        if status:
            proposals = [p for p in proposals if p.status == status]
        
        return [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status.value,
                "domains": p.domains,
                "novelty_score": p.novelty_score,
                "created_at": p.created_at.isoformat()
            }
            for p in proposals
        ]
    
    def update_status(self, proposal_id: str, new_status: ProposalStatus) -> bool:
        """Update proposal status"""
        if proposal_id not in self.proposals:
            return False
        
        self.proposals[proposal_id].status = new_status
        self.proposals[proposal_id].updated_at = datetime.now()
        return True
    
    def export_proposal_markdown(self, proposal_id: str) -> Optional[str]:
        """Export proposal as Markdown"""
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        
        md = f"""# {proposal.title}

**Proposal ID:** {proposal.id}  
**Status:** {proposal.status.value}  
**Created:** {proposal.created_at.strftime('%Y-%m-%d')}  

---

## Abstract

{proposal.abstract}

---

## Source Insight

> {proposal.source_insight_content}

**Novelty Score:** {proposal.novelty_score:.2f}  
**Testability Score:** {proposal.testability_score:.2f}

---

## Hypothesis

**Primary Hypothesis:**  
{proposal.hypothesis}

**Null Hypothesis:**  
{proposal.null_hypothesis}

---

## Research Questions

"""
        for i, q in enumerate(proposal.research_questions, 1):
            md += f"{i}. {q}\n"
        
        md += """
---

## Objectives

"""
        for i, o in enumerate(proposal.objectives, 1):
            md += f"{i}. {o}\n"
        
        md += f"""
---

## Methodology

**Approach:** {proposal.methodology.get('approach', 'N/A')}

**Methods:**
"""
        for m in proposal.methodology.get('methods', []):
            md += f"- {m}\n"
        
        md += f"""
**Data Collection:**
"""
        for d in proposal.methodology.get('data_collection', []):
            md += f"- {d}\n"
        
        md += f"""
---

## Experimental Design

{proposal.experimental_design}

### Variables

**Independent Variables:**
"""
        for v in proposal.variables.get('independent', []):
            md += f"- {v}\n"
        
        md += """
**Dependent Variables:**
"""
        for v in proposal.variables.get('dependent', []):
            md += f"- {v}\n"
        
        md += """
**Controlled Variables:**
"""
        for v in proposal.variables.get('controlled', []):
            md += f"- {v}\n"
        
        md += f"""
---

## Timeline

**Estimated Duration:** {proposal.estimated_duration_weeks} weeks

| Phase | Milestone | Duration | Deliverables |
|-------|-----------|----------|--------------|
"""
        for m in proposal.milestones:
            deliverables = ", ".join(m.deliverables[:2])
            md += f"| {m.phase.value} | {m.name} | {m.estimated_weeks} weeks | {deliverables} |\n"
        
        md += f"""
---

## Resources

**Estimated Budget:** ${proposal.estimated_budget:,.2f}

| Category | Resource | Estimated Cost | Availability |
|----------|----------|----------------|--------------|
"""
        for r in proposal.resources:
            cost = f"${r.estimated_cost:,.2f}" if r.estimated_cost else "N/A"
            md += f"| {r.category} | {r.name} | {cost} | {r.availability} |\n"
        
        md += f"""
---

## Expected Outcomes

"""
        for i, o in enumerate(proposal.expected_outcomes, 1):
            md += f"{i}. {o}\n"
        
        md += f"""
---

## Potential Impact

{proposal.potential_impact}

---

## Success Metrics

"""
        for i, s in enumerate(proposal.success_metrics, 1):
            md += f"{i}. {s}\n"
        
        md += """
---

## Risk Assessment

| Risk | Mitigation | Severity |
|------|------------|----------|
"""
        for r in proposal.risk_assessment:
            md += f"| {r['risk']} | {r['mitigation']} | {r['severity']} |\n"
        
        md += f"""
---

## Keywords

{', '.join(proposal.keywords)}

---

*Generated by UnifiedAi Research Proposal Generator*
"""
        
        return md


# Global instance
research_generator = ResearchProposalGenerator()

