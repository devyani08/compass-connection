import streamlit as st
import json
import re
import os
from pymongo import MongoClient
from bson import ObjectId  # Import ObjectId
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

# Function to connect to MongoDB and fetch Markdown content from all matching job_ids
def fetch_markdown_from_db(job_id):
    mongo_uri = os.getenv("MONGODB_URI", st.secrets["MONGODB_URI"])
    client = MongoClient(mongo_uri)
    db = client["parsing-data"]
    collection = db["data_1"]

    # Use ObjectId to query the job_id if it's an ObjectId type in MongoDB
    documents = collection.find({"job_id": ObjectId(job_id)})

    content_list = []  # List to store all content from matching documents
    for document in documents:
        content = document.get("content")
        if content:
            content_list.append(content)

    if content_list:
        return content_list
    else:
        return f"Job ID {job_id} not found in the database."

# Function to extract recommendations from Markdown content (if table format exists)
def extract_recommendations_from_table(md_content):
    lines = md_content.splitlines()
    table_lines = [line for line in lines if "|" in line and not line.startswith("|---")]

    recommendations = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) == 3:
            cor, loe, recommendation = cells
            if cor.lower() == "cor" and loe.lower() == "loe":
                continue
            recommendations.append({
                "recommendation_content": recommendation.strip(),
                "recommendation_class": cor.strip(),
                "rating": loe.strip()
            })

    return recommendations

# Function to extract recommendations from regular Markdown content (non-table)
def extract_recommendations_from_plain_text(md_content):
    # For plain text, you might extract recommendations based on some keywords or patterns
    # Example: If you know there are specific keywords to extract, use regex or string matching here.
    recommendations = []
    # Placeholder logic for plain text processing (customize as needed)
    if "recommendation:" in md_content.lower():
        recommendations.append({
            "recommendation_content": md_content.strip(),
            "recommendation_class": "General",  # Or some default class
            "rating": "N/A"  # Or set appropriate default
        })
    return recommendations

# Function to generate JSON chunks
def generate_json_chunks(recommendations, title, stage, disease, specialty):
    base_json = {
        "title": title,
        "subCategory": [],
        "guide_title": title,
        "stage": [stage],
        "disease": [disease],
        "rationales": [],
        "references": [],
        "specialty": [specialty]
    }

    json_chunks = []
    for rec in recommendations:
        chunk = base_json.copy()
        chunk.update({
            "recommendation_content": rec["recommendation_content"],
            "recommendation_class": rec["recommendation_class"],
            "rating": rec["rating"]
        })
        json_chunks.append(chunk)

    return json_chunks

# Streamlit app
st.title("Markdown to JSON Converter")

# Metadata Inputs
st.header("Enter Metadata for Recommendations")
title = st.text_input("Guide Title", "Distal Radius Fracture Rehabilitation")
stage = st.text_input("Stage", "Rehabilitation")
disease = st.text_input("Disease Title", "Fracture")
specialty = st.text_input("Specialty", "orthopedics")

# Job ID input (Mandatory)
job_id = st.text_input("Job ID (mandatory for MongoDB)")

if job_id:
    md_contents = fetch_markdown_from_db(job_id)
    
    if isinstance(md_contents, list) and md_contents:  # If we got a list of contents
        st.write(f"{len(md_contents)} documents found with Job ID {job_id}.")
        all_recommendations = []
        
        # Iterate over each content and extract recommendations
        for md_content in md_contents:
            # Check if the content contains a table
            if "|" in md_content:  # If the content appears to be in table format
                recommendations = extract_recommendations_from_table(md_content)
            else:  # If the content does not appear to have a table, process it as plain text
                recommendations = extract_recommendations_from_plain_text(md_content)
            
            all_recommendations.extend(recommendations)  # Add to the main list of recommendations

        if all_recommendations:
            json_chunks = generate_json_chunks(all_recommendations, title, stage, disease, specialty)

            st.subheader("Generated JSON:")
            st.json(json_chunks)

            json_output = json.dumps(json_chunks, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_output,
                file_name="output.json",
                mime="application/json"
            )
        else:
            st.warning("No recommendations found in the fetched Markdown content.")
    else:
        st.warning(f"Job ID {job_id} not found in the database.")
else:
    st.info("Please enter a Job ID to fetch data from the database.")
