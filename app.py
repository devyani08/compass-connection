import streamlit as st
import json
import re
from pymongo import MongoClient

# Function to connect to MongoDB and fetch Markdown content
def fetch_markdown_from_db(job_id):
    # Set up MongoDB client and fetch data
    client = MongoClient("mongodb://localhost:27017/")
    db = client["document-parsing"] 
    collection = db["dps_data"]

    # Fetch the document based on job_id
    document = collection.find_one({"job_id": job_id})
    
    # Return the Markdown content (assuming it’s stored in the 'category' field)
    return document.get("category") if document else None

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

# File uploader
st.header("Upload Markdown File or Enter Job ID")
uploaded_file = st.file_uploader("Upload a Markdown (.md) file", type=["md"])
job_id = st.text_input("Job ID (optional, for MongoDB)")

if uploaded_file is not None:
    # Read the file content
    md_content = uploaded_file.read().decode("utf-8")
    st.write("Markdown file content loaded successfully.")

elif job_id:
    # Fetch the Markdown content from MongoDB based on job_id
    md_content = fetch_markdown_from_db(job_id)
    if md_content:
        st.write("Markdown content fetched from MongoDB.")
    else:
        st.warning(f"Job ID {job_id} not found in the database.")

else:
    st.info("Please upload a Markdown file or enter a Job ID to begin.")

if md_content:
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
        st.warning("No recommendations found in the uploaded file. Please check the file format.")
