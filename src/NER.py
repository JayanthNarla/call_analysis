# process_transcripts_azure.py

import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
import re
from dotenv import load_dotenv

load_dotenv()

# Azure Text Analytics API details
endpoint = os.getenv('TEXT_ENDPOINT')
key = os.getenv('TEXT_KEY')

# Folder where transcripts are saved
RECORDINGS_FOLDER = "data/wav_recordings"
PROCESSED_FOLDER = "data/NER"

def initialize_language_client():
    credential = AzureKeyCredential(key)
    return TextAnalyticsClient(endpoint=endpoint, credential=credential)

def process_transcript_file(file_path, language_client):
    print(f"Processing file: {file_path}")
    
    with open(file_path, 'r') as f:
        transcript_text = f.read()

    # Step 1: Azure NER
    azure_result = language_client.recognize_entities(documents=[transcript_text])[0]
    azure_entities = [
        {
            "text": entity.text,
            "category": entity.category,
            "subcategory": entity.subcategory,
            "confidence_score": entity.confidence_score,
        } for entity in azure_result.entities
    ]

    # Step 2: Custom 911-specific entity extraction
    custom_entities = extract_911_entities(transcript_text)

    results = {
        "transcript": transcript_text,
        "azure_entities": azure_entities,
        "911_entities": custom_entities
    }

    return results

def extract_911_entities(text):
    entities = {
        "location": extract_location(text),
        "emergency_type": extract_emergency_type(text),
        "caller_info": extract_caller_info(text),
        "victim_info": extract_victim_info(text),
        "suspect_description": extract_suspect_description(text),
        "vehicle_description": extract_vehicle_description(text),
        "injuries": extract_injuries(text),
        "weapons": extract_weapons(text),
        "incident_time": extract_incident_time(text)
    }
    return {k: v for k, v in entities.items() if v is not None}

def extract_location(text):
    patterns = [
        r"at (\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd))",
        r"on ([\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd))",
        r"in ([\w\s]+(?:Park|Building|Mall|Center|Centre))",
        r"near ([\w\s]+(?:landmark|intersection|cross street))"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def extract_emergency_type(text):
    emergency_types = {
        "fire": ["fire", "burning", "smoke"],
        "medical": ["medical", "heart attack", "breathing", "unconscious"],
        "accident": ["accident", "crash", "collision"],
        "crime": ["robbery", "assault", "break-in", "shooting"],
        "missing person": ["missing", "disappeared", "can't find"]
    }
    for e_type, keywords in emergency_types.items():
        if any(keyword in text.lower() for keyword in keywords):
            return e_type
    return None

def extract_caller_info(text):
    name_match = re.search(r"(?:my name is|this is) ([\w\s]+)", text, re.IGNORECASE)
    phone_match = re.search(r"(?:my (?:phone|number) is|you can reach me at) (\d{3}[-.\s]?\d{3}[-.\s]?\d{4})", text, re.IGNORECASE)
    info = {}
    if name_match:
        info['name'] = name_match.group(1)
    if phone_match:
        info['phone'] = phone_match.group(1)
    return info if info else None

def extract_victim_info(text):
    patterns = [
        r"(?:victim|injured person|patient) (?:is|appears to be) (?:a )?([\w\s]+)",
        r"(?:victim|injured person|patient) (?:is|appears to be) (?:approximately )?((?:\d+|a few|several) years old)",
        r"(male|female) (?:victim|patient|person)"
    ]
    info = {}
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['description'] = match.group(1)
            break
    return info if info else None

def extract_suspect_description(text):
    patterns = [
        r"suspect (?:is|looks like) ([\w\s]+)",
        r"(?:wearing|dressed in) ([\w\s]+)",
        r"(?:approximately )?((?:\d+|a few|several) years old)",
        r"(male|female) suspect"
    ]
    description = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            description.append(match.group(1))
    return " ".join(description) if description else None

def extract_vehicle_description(text):
    pattern = r"(?:vehicle|car|truck) (?:is |looks like )?((?:a |an )?[\w\s]+)(?:license plate|tag)? (?:number |is |reads )?([\w\d]+)?"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return {
            "description": match.group(1).strip(),
            "license_plate": match.group(2) if match.group(2) else None
        }
    return None

def extract_injuries(text):
    injury_keywords = ["injured", "bleeding", "unconscious", "pain", "wound"]
    injuries = [keyword for keyword in injury_keywords if keyword in text.lower()]
    return injuries if injuries else None

def extract_weapons(text):
    weapon_keywords = ["gun", "knife", "weapon", "firearm", "blade"]
    weapons = [keyword for keyword in weapon_keywords if keyword in text.lower()]
    return weapons if weapons else None

def extract_incident_time(text):
    patterns = [
        r"(?:at|around|about) (\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)",
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?) (?:today|yesterday|this morning|this afternoon|this evening|tonight)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def save_results(results, original_filename):
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    output_filename = os.path.join(PROCESSED_FOLDER, f"{base_name}_processed.json")
    with open(output_filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_filename}")

def main():
    language_client = initialize_language_client()
    for filename in os.listdir(RECORDINGS_FOLDER):
        if filename.endswith(".txt"):
            file_path = os.path.join(RECORDINGS_FOLDER, filename)
            results = process_transcript_file(file_path, language_client)
            save_results(results, filename)

if __name__ == "__main__":
    main()