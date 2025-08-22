# local_models.py
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

class LocalModelFallback:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.setup_model()
    
    def setup_model(self):
        """Setup a local model as fallback"""
        try:
            # Use a smaller model that can run on CPU
            self.model = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-medium",
                tokenizer="microsoft/DialoGPT-medium",
                torch_dtype=torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            self.has_local_model = True
        except Exception as e:
            print(f"Failed to load local model: {e}")
            self.has_local_model = False
    
    def generate_response(self, message: str, conversation_history: list = None) -> str:
        """Generate response using local model"""
        if not self.has_local_model:
            return "I'm currently unable to process your request due."
        
        try:
            # Format conversation history
            if conversation_history:
                context = " ".join([f"{'User' if role == 'user' else 'Assistant'}: {content}" 
                                  for role, content, _ in conversation_history[-3:]])
                prompt = f"{context}\nUser: {message}\nAssistant:"
            else:
                prompt = f"User: {message}\nAssistant:"
            
            # Generate response
            response = self.model(
                prompt,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.model.tokenizer.eos_token_id
            )
            
            return response[0]['generated_text'].replace(prompt, "").strip()
        except Exception as e:
            return f"I encountered an error with the local model: {str(e)}. Please try again later."