import json

syllabus = json.loads(open("pipeline\\data\\processed\\COMP3223\\COMP3223_syllabus.json").read())
# dict_keys(['title', 'module_code', 'academic_year', 'semester', 'level', 
# 'credits', 'module_lead', 'exclusions', 'overview', 
# 'aims_and_objectives', 'syllabus', 'teaching', 'resources', 'assessment'])

# print(syllabus["module"].keys())

# print(syllabus["module"]["syllabus"]["topics"])

# topic_dict = {}

# for topic in syllabus["module"]["syllabus"]["topics"]:
#     topic_name = topic["title"]
#     topic_desc = topic["subtopics"]
#     topic_dict[topic_name] = topic_desc

# # print(topic_dict)

# from transformers import pipeline
# print("Loading model...")
# classifier = pipeline("zero-shot-classification",
#                       model="facebook/bart-large-mnli")

# #  TODO: this classification is not aware of overall syllabus, so classification doesn't reflect relative difficulty within the module.

# for i,j in topic_dict.items():
#     sequence_to_classify = f"Module: {syllabus['module']['title']}\nTopic: {i}\nSubtopics: {j}"
#     candidate_labels = ['easy', 'intermediate', 'hard']
#     var = classifier(sequence_to_classify, candidate_labels)
    
#     top_label = var['labels'][0]
#     top_score = var['scores'][0]
    
#     print(f"Topic: {i}")
#     print(f"Subtopics: {j}")
#     print(f"Hardness: {top_label} ({top_score:.2%})")
#     print("-" * 20)


# # sequence_to_classify = "one day I will see the world"
# # candidate_labels = ['introductory', 'intermediate', 'advanced']
# # var = classifier(sequence_to_classify, candidate_labels)
# # print(var)

# Scrap idea with zero shot for now, or sbert. After tests they don't work good on data
# embed semantics hardness within json of syllabus in syllabus llm parsing for now. 
# in future could be replaced by api call to smaller models


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
This is needed for semantic understanding of difficulty, as the syllabus descriptions are not standardised and may contain noisy information

Input:  [Module Name] + [Topic Name] + [Syllabus Description] (context prevents noisy garbage classification)
Model:  facebook/bart-large-mnli
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