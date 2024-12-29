import streamlit as st
import requests
import json
import uuid

# Configure the base URL for your FastAPI backend
BASE_URL = "https://testing.murshed.marahel.sa/"

def is_valid_uuid(val):
    """Check if the string is a valid UUID"""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def main():
    st.title("MARAHEL QA ChatBot")
    
    # Initialize session state variables if they don't exist
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'last_response' not in st.session_state:
        st.session_state.last_response = None
    if 'last_question' not in st.session_state:
        st.session_state.last_question = None
    if 'chatbot_id' not in st.session_state:
        st.session_state.chatbot_id = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    # Create tabs for different sections
    chat_tab, regeneration_tab = st.tabs(["Chat Interface", "Response Regeneration"])

    # Sidebar for configuration and file upload
    with st.sidebar:
        st.header("Configuration")
        
        # Chatbot ID input or generation
        col1, col2 = st.columns([2, 1])
        with col1:
            entered_id = st.text_input("Enter Chatbot ID (UUID format):", value=st.session_state.chatbot_id if st.session_state.chatbot_id else "")
            if entered_id:
                if is_valid_uuid(entered_id):
                    st.session_state.chatbot_id = entered_id
                else:
                    st.error("Please enter a valid UUID format")
                    st.session_state.chatbot_id = None
        with col2:
            if st.button("Generate ID"):
                st.session_state.chatbot_id = str(uuid.uuid4())
        
        if st.session_state.chatbot_id:
            st.info(f"Chatbot ID: {st.session_state.chatbot_id}")
            
        # User ID input
        user_id = st.text_input("Enter User ID", key="user_id_input", value=st.session_state.user_id if st.session_state.user_id else "")
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
            if not st.session_state.chatbot_id or not st.session_state.user_id:
                st.error("Please enter both Chatbot ID and User ID before processing documents.")
            else:
                with st.spinner("Processing documents..."):
                    try:
                        files = [
                            ('files', (file.name, file.read(), file.type))
                            for file in uploaded_files
                        ]
                        
                        # Include all required parameters in the form data
                        form_data = {
                            "chatbot_id": st.session_state.chatbot_id,
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
                        "chatbot_id": st.session_state.chatbot_id,
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
                    json={"chatbot_id": st.session_state.chatbot_id}
                )
                if response.status_code == 200:
                    st.success("Collection deleted successfully!")
                    st.session_state.chat_history = []
                else:
                    st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
            except Exception as e:
                st.error(f"Error deleting collection: {str(e)}")
    
    if not user_id or not st.session_state.chatbot_id:
        st.info("Please enter User ID and Chatbot ID to start chatting.")
        return

    # Chat Interface Tab
    with chat_tab:
        # Create a container for the chat history that takes up most of the space
        chat_container = st.container()
        
        # Create a container for the input box at the bottom
        input_container = st.container()
        
        # Handle the input first (but it will appear at the bottom)
        with input_container:
            st.markdown("<div style='padding: 1rem; background-color: #f0f2f6; position: fixed; bottom: 0; right: 0; left: 0; z-index: 1000;'>", unsafe_allow_html=True)
            prompt = st.chat_input("Ask a question about your documents")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if prompt:
                # Get AI response
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/chat-bot",
                        json={
                            "query": prompt,
                            "chatbot_id": st.session_state.chatbot_id,
                            "user_id": user_id
                        }
                    )
                    
                    if response.status_code == 200:
                        ai_response = response.json()["data"]
                        
                        # Add messages to chat history
                        st.session_state.chat_history.append({"role": "user", "content": prompt})
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                        st.session_state.last_response = ai_response
                        st.session_state.last_question = prompt
                        
                        # Rerun to update the chat history display
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
                except Exception as e:
                    st.error(f"Error getting response: {str(e)}")
        
        # Display chat history in the main container
        with chat_container:
            st.markdown("<div style='margin-bottom: 100px'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)

    # Response Regeneration Tab
    with regeneration_tab:
        st.subheader("Response Regeneration")
        
        # Three independent input fields
        col1, col2 = st.columns([1, 1])
        with col1:
            question = st.text_area("Enter the question", height=150, key="regen_question")
        with col2:
            original_response = st.text_area("Enter the response to regenerate", height=150, key="regen_response")
        
        instructions = st.text_area("Enter instructions for regenerating the response", height=100, key="regen_instructions")
        
        if st.button("Regenerate Response", key="regenerate_button"):
            if not question or not original_response or not instructions:
                st.warning("Please fill in all fields (question, response, and instructions).")
            else:
                try:
                    response = requests.post(
                        f"{BASE_URL}/api/response-regeneration",
                        json={
                            "question": question,
                            "instructions": instructions,
                            "response": original_response
                        }
                    )
                    if response.status_code == 200:
                        regenerated_response = response.json()["data"]
                        st.success("Response regenerated successfully!")
                        st.markdown("### Regenerated Response:")
                        st.write(regenerated_response)
                    else:
                        st.error(f"Error: {response.json().get('message', 'Unknown error occurred')}")
                except Exception as e:
                    st.error(f"Error regenerating response: {str(e)}")

if __name__ == "__main__":
    main()
