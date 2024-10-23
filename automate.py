import os
from openai import OpenAI
from dotenv import load_dotenv
import base64
import requests

load_dotenv()

assistant_id = os.getenv("ASSISTANT_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# FUNCTION TO request appropriate paths, subject to change if too complicated
def get_valid_file_path(prompt):
    while True:
        path = input(prompt)
        if os.path.isfile(path):
            return path
        else:
            print("Invalid file path. Please try again.")

def get_valid_directory_path(prompt):
    while True:
        path = input(prompt)
        if os.path.isdir(path):
            return path
        else:
            print("Invalid directory path. Please try again.")

# for encoding
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

#calls function, saves appropriate paths
pptx_file_path = get_valid_file_path("Please enter the path to the PPTX file: ")
image_folder_path = get_valid_directory_path("Please enter the path to the image folder: ")
script_folder_title = input("Please enter the title for the script folder: ")
script_folder_path = get_valid_directory_path("Please enter the file path for the new folder to be generated: ")

# Create the new folder for scripts using the script_folder_title
output_folder_path = os.path.join(script_folder_path, script_folder_title)
os.makedirs(output_folder_path, exist_ok=True)

#the main prompts that will be used for the presentation
prompt1 = "please summarize this presentation"
prompt2 = "please list the title and summary of each slide"
mainPrompt = (
    "I am making a recording of this presentation. Please generate a very detailed script for this slide. "
    "Only include the text for the script. Do not include any other instructions, headings, or commentary about the script. "
    "Please be verbose. Generate the script as if people can't see the symbols. "
    "Pronounce any symbolic connectives or well-formed formulas as if you were telling someone to write them on a chalkboard."
)

#prepares file, should change to with open
message_file = client.files.create(
    file=open(pptx_file_path, "rb"), purpose="assistants"
)

# first prompt  created
thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": prompt1,
            "attachments": [
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ],
        }
    ]
)

#first prompt processed
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, 
    assistant_id=assistant_id
)

messages = client.beta.threads.messages.list(thread_id=thread.id)
summary = messages.data[0].content[0].text.value

# Get slide titles and summaries
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=prompt2
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, 
    assistant_id=assistant_id
)

messages = client.beta.threads.messages.list(thread_id=thread.id)
slide_info = messages.data[0].content[0].text.value

# Function to process image with Vision API
def process_image_with_vision(image_path, slide_number, summary, slide_info):
    base64_image = encode_image(image_path)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"This is slide {slide_number} of a presentation. Here's a summary of the entire presentation: {summary}\n\nHere's information about all slides: {slide_info}\n\n{mainPrompt}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 900
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

# Process each image
for index, imagefile in enumerate(os.listdir(image_folder_path)):
    file_name = f"{script_folder_title}_{index+1}.txt"
    file_path = os.path.join(image_folder_path, imagefile)
    
    script_content = process_image_with_vision(file_path, index + 1, summary, slide_info)
    
    # Save to the new folder created with script_folder_title
    text_file_path = os.path.join(output_folder_path, file_name)
    with open(text_file_path, "w") as text_file:
        text_file.write(script_content)
    
    print(f"Processed slide {index + 1}")

print("All slides processed successfully!")