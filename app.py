import os
import openai
import streamlit as st
from dotenv import load_dotenv
from render import bot_msg_container_html_template, user_msg_container_html_template 
from streamlit_chat import message
from utils import semantic_search
import prompts
from pinecone import Pinecone
#Set up OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]
pinecone_api_key = st.secrets["PINECONE_API_KEY"]
pinecone_env = "gcp-starter"
pinecone_name = "test"

pc = Pinecone(
    api_key = os.environ.get(st.secrets["PINECONE_API_KEY"]),
    
)
# pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
# index = pinecone.Index(pinecone_name)

st.header("English Education GPT - Chat with a Teacher")

# Define chat history storage
if "history" not in st.session_state:
    st.session_state.history = []

#Construct messages from chat history
def construct_messages(history):
    messages = [{"role" : "system", "content":prompts.system_message}]

    for entry in history:
        role = "user" if entry["is_user"] else "assistant"
        messages.append({"role" : role, "content" : entry["message"]})

    return messages

#Generate response to user prompt
def generate_response():
    st.session_state.history.append({
        "message" : st.session_state.prompt,
        "is_user" : True
    })

    print(f"Answer : {st.session_state.prompt}")

    #Perform semantic search and format results
    search_results = semantic_search(st.session_state.prompt, index, top_k = 3)

    print(f"Results: {search_results}")

    context = ""
    for i, (source, transcript) in enumerate(search_results):
        context += f"Snippet from: {source}\n {transcript}\n\n"

    #Generate human prompt template and converty to API message format
    query_with_context = prompts.human_template.format(query = st.session_state.prompt, context=context)

    #Convert chat history to a list of messages
    messages = construct_messages(st.session_state.history)
    messages.append({"role" : "user", "content":query_with_context})

    #Run the LLMChain
    response = openai.chat.completions.create(model="gpt-4-0125-preview", messages=messages)
    print(response)

    #Parse response
    bot_response = response["choices"][0]["message"]["content"]
    st.session_state.history.append({
        "message" : bot_response,
        "is_user" : False
    })

    #User input prompt
    user_prompt = st.text_input("Enter your prompt: ",
                                key="prompt",
                                placeholder="e.g. 'Write me a business plan to scale my coaching business.'",
                                on_change=generate_response)
    
    #Display chat history
    for message in st.session_state.history:
        if message["is_user"]:
            st.write(user_msg_container_html_template.replace("$MSG", message["message"]), unsafe_allow_html=True)
        else:
            st.write(bot_msg_container_html_template.replace("$MSG", message["message"]), unsafe_allow_html=True)
