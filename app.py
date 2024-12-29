import streamlit as st
import requests
import json
import uuid

# Configure the base URL for your FastAPI backend
BASE_URL = "http://127.0.0.1:9696/"  #

# Hardcoded chatbot ID
# CHATBOT_ID = "f6b19aa2-b147-4ca1-8f4a-f4470866a5a0"

def main():
    st.title("MARAHEL QA ChatBot")
    
    # Initialize session state variables if they don't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'last_response' not in st.session_state:
        st.session_state.last_response = None
    if 'last_question' not in st.session_state:
        st.session_state.last_question = None

    # Sidebar for configuration and file upload
    with st.sidebar:
        st.header("Configuration")
        
         # Chatbot ID input
        chatbot_id = st.text_input("Enter Chatbot ID", key="chatbot_id_input")
        if chatbot_id:
            st.session_state.chatbot_id = chatbot_id
        else:
            st.warning("Please enter a uuid as Chatbot ID.")
            
        # User ID input
        user_id = st.text_input("Enter User ID", key="user_id_input")
        if user_id:
            st.session_state.user_id = user_id
        
        # LLM Model selection
        llm_model = st.selectbox(
            "Select LLM Model",
            ["openai", "claude"]
        )
        
        # File upload section
        st.subheader("Document Upload")
        uploaded_files = st.file_uploader(
            "Upload Documents",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'doc']
        )
        
        # Database selection
        vectorstore_database = st.selectbox(
            "Select Vector Database",
            ["qdrant", "pgvector"]
        )
        
        # Model selection
        embeddings_model = st.selectbox(
            "Select Embeddings Model",
            [
                "asafaya/bert-base-arabic",
                "Omartificial-Intelligence-Space/Arabic-mpnet-base-all-nli-triplet",
                "Omartificial-Intelligence-Space/Arabic-Triplet-Matryoshka-V2",
                "openai"
            ]
        )

        # Chunking parameters
        chunk_size = st.number_input("Chunk Size", min_value=100, value=1000)
        chunk_overlap = st.number_input("Chunk Overlap", min_value=0, value=200)
        
        if uploaded_files and st.button("Process Documents"):
            with st.spinner("Processing documents..."):
                try:
                    files = [
                        ('files', (file.name, file.read(), file.type))
                        for file in uploaded_files
                    ]
                    
                    # Include all required parameters in the form data
                    form_data = {
                        "chatbot_id": chatbot_id,
                        "chunk_size": str(chunk_size),
                        "chunk_overlap": str(chunk_overlap),
                        "embeddings_model": embeddings_model,
                        "vectorstore_name": vectorstore_database,
                        "llm": llm_model
                    }
                    
                    response = requests.post(
                        f"{BASE_URL}/api/Ingestion_File",
                        files=files,
                        data=form_data
                    )
                    
                    if response.status_code == 200:
                        st.success("Documents processed successfully!")
                    else:
                        st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
                        
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")

        # Custom Instructions Section
        st.subheader("Custom Instructions")
        guidelines = st.text_area("Guidelines")
        user_input = st.text_area("User Input Example")
        user_output = st.text_area("Expected Output Example")
        
        if st.button("Save Custom Instructions"):
            try:
                response = requests.post(
                    f"{BASE_URL}/api/custom-instruction",
                    json={
                        "chatbot_id": chatbot_id,
                        "guidelines": guidelines,
                        "user_input": user_input,
                        "user_output": user_output
                    }
                )
                if response.status_code == 200:
                    st.success("Custom instructions saved successfully!")
                else:
                    st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
            except Exception as e:
                st.error(f"Error saving custom instructions: {str(e)}")
        
        # Delete collection button
        if st.button("Delete Current Collection"):
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/delete-collection",
                    json={"chatbot_id": chatbot_id}
                )
                if response.status_code == 200:
                    st.success("Collection deleted successfully!")
                    st.session_state.chat_history = []
                else:
                    st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
            except Exception as e:
                st.error(f"Error deleting collection: {str(e)}")
    
    if not user_id:
        st.info("Please enter User ID to start chatting.")
        return
        
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                st.write(message["content"]["response"])
                with st.expander("View Sources"):
                    for source in message["content"]["source"]:
                        st.write(f"Document: {source['documents']['filename']}")
                        st.write(f"Pages: {', '.join(map(str, source['documents']['pages']))}")
            else:
                st.write(message["content"])

    # Response Regeneration Section
    if st.session_state.last_response and st.session_state.last_question:
        st.subheader("Response Regeneration")
        instructions = st.text_area("Enter instructions for regenerating the response")
        if st.button("Regenerate Response"):
            try:
                response = requests.post(
                    f"{BASE_URL}/api/response-regeneration",
                    json={
                        "question": st.session_state.last_question,
                        "instructions": instructions,
                        "response": st.session_state.last_response["response"] if isinstance(st.session_state.last_response, dict) else st.session_state.last_response
                    }
                )
                if response.status_code == 200:
                    regenerated_response = response.json()["data"]
                    with st.chat_message("assistant"):
                        st.write(regenerated_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": regenerated_response})
                else:
                    st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
            except Exception as e:
                st.error(f"Error regenerating response: {str(e)}")

    # Chat input
    if prompt := st.chat_input("Ask a question about your documents"):
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.last_question = prompt
        
        # Get AI response
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat-bot",
                json={
                    "query": prompt,
                    "chatbot_id": chatbot_id,
                    "user_id": user_id
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()["data"]
                # Display AI response
                with st.chat_message("assistant"):
                    st.write(ai_response["response"])
                    with st.expander("View Sources"):
                        for source in ai_response["source"]:
                            st.write(f"Document: {source['documents']['filename']}")
                            st.write(f"Pages: {', '.join(map(str, source['documents']['pages']))}")
                # Add AI response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                st.session_state.last_response = ai_response
            else:
                st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
        except Exception as e:
            st.error(f"Error getting response: {str(e)}")

if __name__ == "__main__":
    main()
