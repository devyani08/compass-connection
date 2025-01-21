import streamlit as st
import json
import re
from pymongo import MongoClient

# Function to connect to MongoDB and fetch Markdown content
def fetch_markdown_from_db(job_id):
   
    client = MongoClient("mongodb+srv://devyani08:devyani08@cluster0.is2at.mongodb.net/")
    db = client["parsing-data"] 
    collection = db["data_1"] 

    # Fetch the document based on job_id
    document = collection.find_one({"job_id": job_id})
    
    if document:
        content = document.get("content")
        if content:
            return content
        else:
            return "Content field is missing in the document."
    else:
        return f"Job ID {job_id} not found in the database."

# Function to extract recommendations from Markdown content
def extract_recommendations(md_content):
    """
    Extract recommendations from Markdown table content.
    """
    # Split content by lines and filter out the header and separator lines
    lines = md_content.splitlines()
    table_lines = [line for line in lines if "|" in line and not line.startswith("|---")]

    recommendations = []
    for line in table_lines:
        # Split the line into cells
        cells = [cell.strip() for cell in line.split("|")[1:-1]]  # Ignore outer empty cells
        if len(cells) == 3:  # Ensure the row has the correct number of columns
            cor, loe, recommendation = cells
            # Skip header row
            if cor.lower() == "cor" and loe.lower() == "loe":
                continue
            recommendations.append({
                "recommendation_content": recommendation.strip(),
                "recommendation_class": cor.strip(),
                "rating": loe.strip()
            })

    return recommendations

# Function to generate JSON chunks
def generate_json_chunks(recommendations, title, stage, disease, specialty):
    """
    Generate JSON chunks using the extracted recommendations and user inputs.
    """
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
    # Fetch the Markdown content from MongoDB based on job_id
    md_content = fetch_markdown_from_db(job_id)
    
    if md_content:
        if md_content.startswith("Content field is missing"):
            st.warning(md_content)
        elif md_content.startswith("Job ID"):
            st.warning(md_content)
        else:
            st.write("Markdown content fetched from MongoDB.")

            # Extract recommendations from the Markdown content
            recommendations = extract_recommendations(md_content)

            if recommendations:
                # Generate JSON chunks using user inputs
                json_chunks = generate_json_chunks(recommendations, title, stage, disease, specialty)

                # Display the JSON chunks
                st.subheader("Generated JSON:")
                st.json(json_chunks)

                # Option to download JSON file
                json_output = json.dumps(json_chunks, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_output,
                    file_name="output.json",
                    mime="application/json"
                )
            else:
                st.warning("No recommendations found in the fetched Markdown content. Please check the file format.")
    else:
        st.warning(f"Job ID {job_id} not found in the database.")
else:
    st.info("Please enter a Job ID to fetch data from the database.")
