import json
from fuzzywuzzy import process

def load_recycling_points():
    with open('data/recycling_points.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def find_waste_item(user_input, waste_dict):
    choices = list(waste_dict.keys())
    best_match, score = process.extractOne(user_input, choices)
    return best_match, score
