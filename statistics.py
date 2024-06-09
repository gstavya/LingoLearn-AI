from pages.App import user_data
from pages.App import user_data2
import streamlit as st

st.title("Statistics")
st.header("Average Score: " + user_data)
st.bar_chart(user_data, color='#FFFFFF')
st.header("Time Spent: " + user_data2)
st.bar_chart(user_data2, color='#FFFFFF')
        
