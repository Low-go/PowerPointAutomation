import os
from openai import OpenAI
from dotenv import load_dotenv

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

#calls function, saves appropriate paths
pptx_file_path = get_valid_file_path("Please enter the path to the PPTX file: ")
# image_folder_path = get_valid_directory_path("Please enter the path to the image folder: ")
# script_folder_title = input("Please enter the title for the script folder: ")
# script_folder_path = get_valid_directory_path("Please enter the file path for the new folder to be generated: ")

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

# second prompt  created
client.beta.threads.messages.create( #messages.create to use existing thread

    thread_id=thread.id,
    role="user",
    content= prompt2
)

#second prompt processed
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, 
    assistant_id=assistant_id
)

messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

message_content = messages[0].content[0].text
annotations = message_content.annotations
citations = []
for index, annotation in enumerate(annotations):
    message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
    if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"[{index}] {cited_file.filename}")

print(message_content.value)
print("\n".join(citations))



# note to self, threads allow conversation context to be maintained
# so i do not have to manually maintain it through an array