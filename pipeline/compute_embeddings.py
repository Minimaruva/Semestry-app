


'''
Hard + important → red, must prioritise
Hard + unimportant → amber, understand it but don't over-invest
Easy + important → amber, quick wins available
Easy + unimportant → green, coast

Sort of Architecture

INPUTS
├── moodle.json       → weeks, topics, lab deadlines
├── syllabus.json     → topic list + descriptions
└── manifest.json     → questions, marks, text, year

STEP 1: Semantic hardness (zero-shot, runs once)
Input:  [Module Name] + [Topic Name] + [Syllabus Description] (context prevents noisy garbage classification)
Model:  facebook/bart-large-mnli on your 1650Ti
Labels: ["introductory", "intermediate", "advanced"]
Output: {topic: hardness_score 0-1}

STEP 2: Topic mapping (Asymmetric/Cross-Encoder, runs once)
Input:  question texts + topic names
Method: embed both, cross-encoder or asymmetric model (e.g., msmarco-distilbert-base-v4) match to handle length asymmetry between 3-word topics and 150-word questions
Output: {topic: [questions mapped to it]}

STEP 3: Exam importance (maths + recency decay)
Input:  mapped questions + their mark allocations + paper year
Formula:
decayed_marks = marks * (recency_decay ^ (current_year - paper_year))
raw_importance = sum(decayed_marks for q in mapped_questions) across all years
normalise 0-1 across all topics
Output: {topic: importance_score 0-1}
Note:   topics with zero mapped questions → importance = 0
"never appeared" signal is explicit

STEP 4: Deadline weight (from moodle)
Input:  lab due dates + lab percentage of total grade
Output: {week: deadline_weight 0-1}

STEP 5: Week danger score
[Standard processing applied]
danger = (hardness × W1) + (importance × W2) + (deadline × W3)
Output: COMP3223_scored.json

'''