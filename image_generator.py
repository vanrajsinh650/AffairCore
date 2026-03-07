import base64

import requests
import urllib.parse
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def generate_visual_prompt_from_context(Gujarati_json_context):
    print("using LLM to understand quiz context and generate visual prompt...")

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    tranucated_context = "\n".join([f"{i+1}. {q['question']}" for i, q in enumerate(Gujarati_json_context[:5])])

    system_instruction = (
        "You are an expert prompt engineer for AI image generators. "
        "Your task is to read the provided Gujarati Current Affairs JSON. "
        "Understand the key topics and visual themes. Summarize the main themes "
        "into a concise, single-paragraph English prompt describing a "
        "professional, clean, flat-design icon or illustration suitable for "
        "a news thumbnail. Do not include any text inside the image. "
        "Focus purely on visual description."
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Gujarati Quiz Context:\n{tranucated_context}\n\nVisual Prompt:"}
            ],
            temperature=0.7,
            max_tokens=200
        )

        visual_summary = completion.choices[0].message.content.strip()
        print(f"Generated visual prompt: {visual_summary}")
        return visual_summary
    
    except Exception as e:
        print(f"Error generating visual prompt: {e}")
        return "daily current affairs news update"

def get_ai_image_url(Gujarati_questions_list):
    ai_visual_prompt = generate_visual_prompt_from_context(Gujarati_questions_list)
    final_prompt = f"Professional clean flat design news icon illustration, topic: {ai_visual_prompt}"

    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

    print(f"generating image using huggingface (FLUX.1)...")

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": final_prompt})

        if response.status_code == 200:
            image_bytes = response.content
            base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            print("Image generated successfully.")
            return base64_encoded_image
        else:
            print(f"Failed to generate image. Status code: {response.status_code}, Response: {response.text}")
            return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None
