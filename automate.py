import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

assistant_id = os.getenv("ASSISTANT_KEY")
# print(assistant_id)
# print(os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



#Create vector store
# vector_store = client.beta.vector_stores.create(name="Temp Document")

# # Upload file
# file_path = r"C:\Users\lorran\Documents\PowerPointAutomation\workflow-files\ch03s1_JG.pptx"

# file_streams = [open(path, "rb") for path in file_path]

# #sdk helper to upload files in vector store
# file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
#     vector_store_id=vector_store.id, file=file_streams
# )

# assistant = client.beta.assistants.update(
#     assistant_id=assistant_id,
#     tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}}
# )

# start from part 4 in the assistants file search documentation




#maybe add a with to close afterwards
message_file = client.files.create(
    file=open(r"C:\Users\lorran\Documents\PowerPointAutomation\workflow-files\ch03s1_JG.pptx", "rb"), purpose="assistants"
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": "please summarize this presentation",
            "attachments":[
                {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
            ],
        }
    ]
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id, assistant_id=assistant_id
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
