import speech_recognition as sr
import pyttsx3
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os
import streamlit as st
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage
import time
from langdetect import detect 

st.title("LingoLearn AI")

load_dotenv()
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-3.5-turbo"
    )

chat_history = []
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant providing feedback on the language the user wants to learn. Ask what level (beginner, intermediate, advanced). MAKE SURE TO CONTINUE THE CONVERSATION with follow-up questions. Emphasize feedback. Give a rating to sentence of the practiced language the user says on a scale of 1 to 10 (no 10s and if in the language being practiced) and provide suggestions. Emphasize SUGGESTIONS and IMPROVEMENTS!",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)
chain = prompt | llm

speech = sr.Recognizer()

try:
    engine = pyttsx3.init()
except ImportError:
    print('Requested driver is not found')
voices = engine.getProperty('voices')
engine.setProperty('voice','HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
engine.setProperty('rate', 175)

def text_to_speech(command):
    response = engine.say(command)
    st.audio(response)
def understand_voice():
    voice_text = ""
    with sr.Microphone() as source:
        st.write("I'm listening ... ")
        audio = speech.listen(source, 6)
    try:
        voice_text = speech.recognize_google(audio, language='es')
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print('Network error.')
    return voice_text

def find_rating(feedback: str) -> int:
    count = 0
    tot = 0
    for i in range (0, len(feedback)-1):
        if feedback[i].isnumeric():
            if int(feedback[i])>1:
                tot += int(feedback[i])
                count += 1
    if count != 0:
        ans =  int(tot)/int(count)
        return ans
    else:
        return 0

user_data = {}
user_data2 = {}
count = 3
feedback = ""
if st.toggle("Start Conversation!"):
    tot = 0
    counter = 0
    start = time.time()
    text_to_speech("Hello, my name is Jarvis. What language would you like to practice today?")
    st.write("Chatbot: Hello, my name is Jarvis. What language would you like to practice today?")
    while True:
        counter += 1
        user_input = understand_voice()
        if "bye" in user_input.lower():
            break
        st.write("You: " + user_input)
        result = chain.invoke({"input": user_input, "chat_history": chat_history})
        chat_history.extend(
                [
                HumanMessage(content=user_input),
                AIMessage(content=result.content),
                ]
            )
        st.write("Chatbot: " + result.content)
        feedback += result.content
        tot += int(find_rating(result.content))
    end = time.time()
    user_data["Conversation " + str(count)] = int(tot/counter)
    user_data2["Conversation " + str(count)] = start-end
    count += 1

    
