import speech_recognition as sr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAI
from dotenv import load_dotenv
import os
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage

import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('key.json')

app = firebase_admin.initialize_app(cred)
db = firestore.client()

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
            """
            You will serve as a native speaker in a specific language. You should know exactly what to talk about (e.g. cars, sports, recent events). Never ask them what they want to talk about. Guide the conversation with specific topics and questions but be brief! Your responses should be relatively short and specific. Max 1-2 sentences!!
            """,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)

prompt2 = ChatPromptTemplate.from_messages([
    ("system", """
    You will be given a conversation with a user and an AI assistant.
    Keep in mind that the conversation is transcribed from an audio, meaning that there will be some "ums" and "ahms." Do not judge the user based on these.
    Your goal is to help the user, as they are not fluent at the language.
    Start with a number from 1 to 10 rating the user's performance. This should be the first character of your response. 1 is horrible, didn't even respond, and 10 is excellent, fluent speaker level.
    Then, provide a list of 3 super specific things that they can improve. No general suggestions. Every suggestion must be followed by a citation of a part of the conversation. Make no suggestions about punctuation, capitalization, or accents, as again, this text you are given is not written by the user, but instead spoken and then written down.
     """),
    MessagesPlaceholder(variable_name="chat_history")
])

prompt3 = ChatPromptTemplate.from_messages([
    ("system", """
    You will be given text in a specific language and will have to return a response translating the text back into English.
    Only return the text back into English, nothing else at all.
    """),
    ("human", "{input}")
])

chain = prompt | llm

summarizer = prompt2 | llm

translator = prompt3 | llm

speech = sr.Recognizer()

import subprocess

def text_to_speech(language, command):
    voice = ""
    if language == "es":
        voice = "Diego"
    elif language == "fr":
        voice = "Aude"
    elif language == "hi":
        voice = "Kiyara"
    else:
        voice = "Daniel"
    subprocess.run(["say", "-v", voice, command])
def understand_voice(language):
    voice_text = ""
    with sr.Microphone() as source:
        print("I'm listening ... ")
        audio = speech.listen(source, 5)
    try:
        voice_text = speech.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print('Network error.')
    return voice_text

import time
    
print("Hello, my name is Jarvis. What language would you like to practice today?")
text_to_speech("en", "Hello, my name is Jarvis. What language would you like to practice today?")
start = time.time()
times_used = 0
all_responses = ""
counter = 0
language = ""
while True:
    counter += 1
    times_used += 1
    if counter == 1:
        user_input = understand_voice(language="en")
        if user_input.lower() == "spanish":
            language = "es"
        if user_input.lower() == "french":
            language = "fr"
        if user_input.lower()=="hendy" or user_input.lower()=="hindi":
            language = "hi"
    else:
        user_input = understand_voice(language=language)
    translated = translator.invoke({"input": user_input}).content
    if "bye" in translated.lower():
        end = time.time()
        db.collection('gstavya').document('stats').update({"time_spent": firestore.Increment(round(end-start,2))})
        db.collection('gstavya').document('stats').update({"plays": firestore.Increment(1)})
        feedback = (summarizer.invoke({"chat_history": chat_history})).content
        db.collection('gstavya').document('stats').update({"tot_score": firestore.Increment(int(feedback[0]))})
        doc = db.collection('gstavya').document('stats').get()
        data = doc.to_dict()
        plays = data.get('plays','')
        tot_score = data.get('tot_score','')
        db.collection('gstavya').document('stats').update({"avg_score": round(tot_score/plays, 2)})
        db.collection('gstavya').document('stats').update({"feedback": firestore.ArrayUnion([feedback])})
        break
    print("You: " + user_input)
    all_responses += user_input
    result = chain.invoke({"input": user_input, "chat_history": chat_history})
    chat_history.extend(
            [
            HumanMessage(content=user_input),
            AIMessage(content=result.content),
            ]
        )
    print("Chatbot: " + result.content)
    text_to_speech(language, result.content)
