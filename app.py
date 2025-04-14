import streamlit as st
import requests
import os
from datetime import datetime
import uuid
from voice import create_voice_interface
from memory_manager import MemoryManager
from three_viewer import create_3d_viewer
import threading
import time

# Set page config
st.set_page_config(
    page_title="AI 3D Generator",
    page_icon="🎨",
    layout="wide"
)

# Constants
API_URL = "http://localhost:8888/generate"

def main():
    st.title("🎨 AI 3D Generator")
    st.markdown("""
    Transform your ideas into 3D models using AI! Enter a prompt, and watch as your imagination comes to life.
    """)
    
    # Initialize memory manager
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = MemoryManager()
    
    # Session management
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Voice interface
    if 'voice_interface' not in st.session_state:
        st.session_state.voice_interface = create_voice_interface()
    
    # Voice input section
    st.sidebar.title("🎤 Voice Input")
    if st.sidebar.button("Start Listening"):
        def update_prompt(text):
            st.session_state.prompt = text
        st.session_state.voice_interface.listen(update_prompt)
        st.sidebar.success("Listening...")
    
    if st.sidebar.button("Stop Listening"):
        st.session_state.voice_interface.stop_listening()
        st.sidebar.info("Stopped listening")
    
    # Similar generations search
    st.sidebar.title("🔍 Similar Generations")
    search_query = st.sidebar.text_input("Search similar generations")
    if search_query:
        similar_results = st.session_state.memory_manager.search_similar(search_query)
        for result in similar_results:
            with st.sidebar.expander(f"Similar: {result['prompt'][:30]}..."):
                st.image(result['metadata']['image_path'])
                st.markdown(f"""
                - **Expanded Prompt**: {result['metadata']['expanded_prompt']}
                - **Created At**: {result['metadata']['timestamp']}
                """)
    
    # Input section
    with st.form("generation_form"):
        prompt = st.text_area(
            "Enter your prompt",
            placeholder="e.g., 'A glowing dragon standing on a cliff at sunset'",
            height=100,
            key="prompt"
        )
        
        submitted = st.form_submit_button("Generate")
    
    if submitted and prompt:
        with st.spinner("Generating your 3D model..."):
            try:
                # Make API request
                response = requests.post(
                    API_URL,
                    json={
                        "prompt": prompt,
                        "session_id": st.session_state.session_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add to memory
                    st.session_state.memory_manager.add_generation(
                        prompt=prompt,
                        expanded_prompt=result["expanded_prompt"],
                        image_path=result["image_path"],
                        model_path=result["model_path"]
                    )
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Generated Image")
                        st.image(result["image_path"])
                    
                    with col2:
                        st.subheader("3D Model")
                        create_3d_viewer(result["model_path"])
                        st.markdown(f"""
                        - **Original Prompt**: {prompt}
                        - **Expanded Prompt**: {result["expanded_prompt"]}
                        - **Model Path**: {result["model_path"]}
                        """)
                        
                        # Add download button for 3D model
                        with open(result["model_path"], "rb") as f:
                            st.download_button(
                                label="Download 3D Model",
                                data=f,
                                file_name=os.path.basename(result["model_path"]),
                                mime="model/gltf-binary"
                            )
                
                else:
                    st.error(f"Error: {response.text}")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    
    # Display history
    st.sidebar.title("📚 Generation History")
    history = st.session_state.memory_manager.get_history()
    for item in history:
        with st.sidebar.expander(f"Prompt: {item['prompt'][:30]}..."):
            st.image(item["image_path"])
            st.markdown(f"""
            - **Expanded Prompt**: {item['expanded_prompt']}
            - **Created At**: {item['timestamp']}
            """)

if __name__ == "__main__":
    main() 