# agentic_engine.py
import os
import time
from langchain.agents import Tool, AgentType, initialize_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import WikipediaAPIWrapper, DuckDuckGoSearchAPIWrapper
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class NeuroSyncAgent:
    def __init__(self):
        self.llm = self.setup_llm()
        self.knowledge_base = []
        self.last_api_call = 0
        self.min_call_interval = 2  # Minimum seconds between API calls
        self.setup_tools()
        self.setup_memory()
        self.setup_agent()
        
    def setup_llm(self):
        """Setup LLM"""
        if not GOOGLE_API_KEY:
            raise ValueError("Prompt not found. Please set it in your.")
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            max_output_tokens=1024,
            google_api_key=GOOGLE_API_KEY
        )

    def rate_limited_call(self, func, *args, **kwargs):
        """Local service failed"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_call_interval:
            time_to_wait = self.min_call_interval - time_since_last_call
            time.sleep(time_to_wait)
        
        try:
            result = func(*args, **kwargs)
            self.last_api_call = time.time()
            return result
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                # Wait longer if we hit rate limit
                time.sleep(5)
                try:
                    result = func(*args, **kwargs)
                    self.last_api_call = time.time()
                    return result
                except Exception as retry_error:
                    raise retry_error
            else:
                raise e

    def setup_tools(self):
        """Setup tools for the agent"""
        # Web Search Tool
        search = DuckDuckGoSearchAPIWrapper()
        
        # Wikipedia Tool
        wikipedia = WikipediaAPIWrapper()
        
        # Calculator Tool
        def calculator(query):
            try:
                # Remove any non-math characters for safety
                cleaned_query = ''.join(c for c in query if c in '0123456789+-*/(). ')
                return str(eval(cleaned_query))
            except:
                return "I couldn't calculate that expression. Please provide a valid mathematical expression."
        
        # Knowledge Base
        def knowledge_search(query):
            if self.knowledge_base:
                return "\n".join([f"{i+1}. {kb}" for i, kb in enumerate(self.knowledge_base[-5:])])
            return "No knowledge available yet."
        
        def add_to_knowledge(fact):
            self.knowledge_base.append(fact)
            return f"Added to knowledge base: {fact}"
            
        # Roadmap Generator
        def generate_roadmap(query):
            roadmap_prompt = f"""
            Create a detailed roadmap for: {query}
            Format it as a step-by-step guide with clear phases and milestones.
            Include estimated timeframes for each phase if possible.
            """
            try:
                return self.rate_limited_call(self.llm.invoke, roadmap_prompt).content
            except Exception as e:
                return f"I couldn't generate a roadmap due to an error."
        
        # Code Helper
        def code_helper(query):
            code_prompt = f"""
            Help with this coding request: {query}
            Provide clear, concise code examples with explanations.
            If it's a complex problem, break it down into steps.
            Format code examples using triple backticks with the language name.
            """
            try:
                return self.rate_limited_call(self.llm.invoke, code_prompt).content
            except Exception as e:
                return f"I couldn't generate code due to an error."

        # Define tools
        self.tools = [
            Tool(
                name="Web Search",
                func=search.run,
                description="Useful for finding current information, news, and facts about recent events. Input should be a search query."
            ),
            Tool(
                name="Wikipedia",
                func=wikipedia.run,
                description="Useful for getting factual information about topics, concepts, people, places, and historical events. Input should be a specific search query."
            ),
            Tool(
                name="Calculator",
                func=calculator,
                description="Useful for performing mathematical calculations and solving equations. Input should be a mathematical expression."
            ),
            Tool(
                name="Knowledge Base",
                func=knowledge_search,
                description="Useful for retrieving information that I've previously stored. Input should be a query about what you want to recall."
            ),
            Tool(
                name="Add Knowledge",
                func=add_to_knowledge,
                description="Useful for storing important information that I should remember for future conversations. Input should be a clear fact or piece of information."
            ),
            Tool(
                name="Roadmap Generator",
                func=generate_roadmap,
                description="Useful for creating step-by-step roadmaps for learning paths, projects, or skill development. Input should be a topic or goal."
            ),
            Tool(
                name="Code Helper",
                func=code_helper,
                description="Useful for assisting with programming and coding problems. Input should be a coding question or problem description."
            )
        ]
    
    def setup_memory(self):
        """Setup conversation memory"""
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,
            return_messages=True,
            output_key="output"
        )
    
    def setup_agent(self):
        """Initialize the agent with tools and memory"""
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )
    
    def generate_response(self, message: str) -> str:
        """Generate a response using the agent"""
        try:
            # Check if user is asking for a roadmap
            roadmap_triggers = ["roadmap", "learning path", "step by step", "plan", "timeline"]
            if any(trigger in message.lower() for trigger in roadmap_triggers):
                # Use the roadmap tool directly
                return self.tools[5].func(message)
                
            # Check if user is asking for code
            code_triggers = ["code", "program", "function", "algorithm", "script", "python", "javascript", "java"]
            if any(trigger in message.lower() for trigger in code_triggers):
                # Use the code helper tool directly
                return self.tools[6].func(message)
                
            response = self.rate_limited_call(self.agent.run, input=message)
            return response
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return "I'm currently facing issue"
            else:
                return f"I am currently facing issue"
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history"""
        return self.memory.load_memory_variables({}).get("chat_history", [])