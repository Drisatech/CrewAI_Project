# agents.py
from crewai import Agent
from crewai.tools import BaseTool
from langchain.llms import OpenAI
import os
from typing import Any

class WordPressInteractionTool(BaseTool):
    name: str = "wordpress_interaction"
    description: str = "Interact with WordPress website for CRUD operations"
    
    def _run(self, action: str, **kwargs) -> str:
        """Execute WordPress actions like post creation, search, user registration"""
        try:
            if action == "search_products":
                return self._search_products(kwargs.get('query', ''))
            elif action == "create_post":
                return self._create_post(kwargs)
            elif action == "register_user":
                return self._register_user(kwargs)
            elif action == "login_user":
                return self._login_user(kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error executing {action}: {str(e)}"
    
    def _search_products(self, query: str) -> str:
        # Implementation for searching products via WordPress API
        import requests
        
        wp_url = os.getenv('WORDPRESS_URL', 'https://farmdepot.ng')
        api_endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        
        params = {
            'search': query,
            'per_page': 10,
            'status': 'publish'
        }
        
        try:
            response = requests.get(api_endpoint, params=params)
            if response.status_code == 200:
                posts = response.json()
                if posts:
                    results = []
                    for post in posts[:5]:  # Limit to 5 results
                        results.append({
                            'title': post['title']['rendered'],
                            'excerpt': post['excerpt']['rendered'][:100] + '...',
                            'link': post['link']
                        })
                    return f"Found {len(results)} products matching '{query}': " + str(results)
                else:
                    return f"No products found for '{query}'"
            else:
                return f"Search failed with status code: {response.status_code}"
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def _create_post(self, post_data: dict) -> str:
        # Implementation for creating posts via WordPress API
        wp_url = os.getenv('WORDPRESS_URL', 'https://farmdepot.ng')
        api_endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        
        auth_header = {
            'Authorization': f"Bearer {os.getenv('WORDPRESS_JWT_TOKEN')}"
        }
        
        post_payload = {
            'title': post_data.get('title', ''),
            'content': post_data.get('content', ''),
            'status': 'publish',
            'categories': post_data.get('categories', [])
        }
        
        try:
            response = requests.post(api_endpoint, json=post_payload, headers=auth_header)
            if response.status_code == 201:
                return "Post created successfully!"
            else:
                return f"Failed to create post: {response.status_code}"
        except Exception as e:
            return f"Post creation error: {str(e)}"
    
    def _register_user(self, user_data: dict) -> str:
        # Implementation for user registration
        wp_url = os.getenv('WORDPRESS_URL', 'https://farmdepot.ng')
        api_endpoint = f"{wp_url}/wp-json/wp/v2/users"
        
        user_payload = {
            'username': user_data.get('username', ''),
            'email': user_data.get('email', ''),
            'password': user_data.get('password', '')
        }
        
        try:
            response = requests.post(api_endpoint, json=user_payload)
            if response.status_code == 201:
                return "User registered successfully!"
            else:
                return f"Registration failed: {response.status_code}"
        except Exception as e:
            return f"Registration error: {str(e)}"
    
    def _login_user(self, credentials: dict) -> str:
        # Implementation for user login
        wp_url = os.getenv('WORDPRESS_URL', 'https://farmdepot.ng')
        api_endpoint = f"{wp_url}/wp-json/jwt-auth/v1/token"
        
        login_payload = {
            'username': credentials.get('username', ''),
            'password': credentials.get('password', '')
        }
        
        try:
            response = requests.post(api_endpoint, json=login_payload)
            if response.status_code == 200:
                token_data = response.json()
                return f"Login successful! Token: {token_data.get('token', '')[:20]}..."
            else:
                return "Login failed: Invalid credentials"
        except Exception as e:
            return f"Login error: {str(e)}"

# Initialize LLM
def get_llm():
    return OpenAI(
        api_key=os.getenv('OPENROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-3.5-turbo"
    )

# Define Agents
def create_agents():
    # WordPress Navigation Agent
    wordpress_agent = Agent(
        role='WordPress Navigation Specialist',
        goal='Help users navigate the FarmDepot.ng classified ads website efficiently',
        backstory="""You are an expert in WordPress navigation and agricultural classified ads. 
                    You understand the Nigerian agricultural market and can help users find what they need on FarmDepot.ng.""",
        tools=[WordPressInteractionTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )
    
    # Product Management Agent
    product_agent = Agent(
        role='Product Management Specialist',
        goal='Assist users in posting, searching, and managing agricultural products on the platform',
        backstory="""You specialize in agricultural products and marketplace operations. 
                    You help farmers, traders, and buyers list their products, search for items, and manage their listings.""",
        tools=[WordPressInteractionTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )
    
    # User Management Agent
    user_agent = Agent(
        role='User Account Specialist',
        goal='Handle user registration, login, and account-related operations',
        backstory="""You manage user accounts and authentication processes. 
                    You help new users register, existing users log in, and resolve account-related issues.""",
        tools=[WordPressInteractionTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False
    )
    
    # Voice Response Agent
    voice_agent = Agent(
        role='Voice Interaction Coordinator',
        goal='Coordinate voice interactions and provide natural language responses',
        backstory="""You coordinate between voice input processing and appropriate responses. 
                    You ensure users get clear, helpful voice responses to their queries.""",
        tools=[],
        llm=get_llm(),
        verbose=True,
        allow_delegation=True
    )
    
    return {
        'wordpress_agent': wordpress_agent,
        'product_agent': product_agent,
        'user_agent': user_agent,
        'voice_agent': voice_agent
    }
