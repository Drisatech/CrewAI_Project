# tasks.py
from crewai import Task
from typing import Dict, Any

def create_tasks(agents: Dict):
    """Create tasks for the CrewAI agents"""
    
    # Task for handling voice commands and routing to appropriate agents
    voice_command_task = Task(
        description="""
        Process incoming voice commands and determine the appropriate action.
        Analyze the user's intent and route to the correct specialist agent.
        
        Voice command: {voice_command}
        
        Possible intents:
        - Product search: "find maize", "search for cassava", "show me rice"
        - Product posting: "post my product", "list my farm produce", "add new item"
        - User registration: "create account", "register", "sign up"
        - User login: "login", "sign in", "access my account"
        - General navigation: "help", "how to use", "what can I do"
        
        Provide a clear response that either:
        1. Answers the query directly
        2. Guides the user to the next step
        3. Asks for clarification if needed
        """,
        agent=agents['voice_agent'],
        expected_output="A clear response addressing the user's voice command with appropriate action taken"
    )
    
    # Task for product-related operations
    product_management_task = Task(
        description="""
        Handle product-related operations on FarmDepot.ng:
        
        Operation: {operation}
        Details: {details}
        
        For product search:
        - Search the database for relevant agricultural products
        - Return results with prices, locations, and contact info
        - Suggest similar products if exact match not found
        
        For product posting:
        - Guide user through posting process
        - Ensure all required fields are provided
        - Validate product information
        - Create the product listing
        
        Provide helpful, agricultural-focused responses suitable for Nigerian farmers and traders.
        """,
        agent=agents['product_agent'],
        expected_output="Successful completion of product operation with clear feedback to user"
    )
    
    # Task for user account operations
    user_management_task = Task(
        description="""
        Handle user account operations on FarmDepot.ng:
        
        Operation: {operation}
        User Data: {user_data}
        
        For registration:
        - Validate user information
        - Create new user account
        - Send welcome message
        - Explain next steps
        
        For login:
        - Authenticate user credentials
        - Create session
        - Welcome user back
        - Show available options
        
        Be helpful and guide users through the process step by step.
        """,
        agent=agents['user_agent'],
        expected_output="Successful user account operation with appropriate response"
    )
    
    # Task for WordPress navigation assistance
    navigation_task = Task(
        description="""
        Help users navigate FarmDepot.ng efficiently:
        
        User Request: {request}
        Current Context: {context}
        
        Provide guidance on:
        - Finding specific sections of the website
        - Understanding how to use features
        - Locating relevant agricultural categories
        - General website orientation
        
        Be specific about Nigerian agricultural context and familiar with:
        - Common crops (maize, cassava, yam, rice, cocoa, etc.)
        - Livestock (cattle, goats, chickens, fish, etc.)
        - Farm equipment and tools
        - Agricultural services
        
        Always be helpful and provide clear directions.
        """,
        agent=agents['wordpress_agent'],
        expected_output="Clear navigation guidance and helpful information for the user"
    )
    
    return {
        'voice_command_task': voice_command_task,
        'product_management_task': product_management_task,
        'user_management_task': user_management_task,
        'navigation_task': navigation_task
    }

def create_dynamic_task(task_type: str, agents: Dict, **kwargs) -> Task:
    """Create a dynamic task based on user input"""
    
    if task_type == "search":
        return Task(
            description=f"""
            Search for agricultural products based on the query: "{kwargs.get('query', '')}"
            
            Use the WordPress interaction tool to search the database.
            Return relevant results with:
            - Product names and descriptions
            - Prices (if available)
            - Seller locations
            - Contact information
            
            If no exact matches, suggest similar products or categories.
            """,
            agent=agents['product_agent'],
            expected_output="Search results with product information"
        )
    
    elif task_type == "post_product":
        return Task(
            description=f"""
            Help user post a new product with the following information:
            Title: {kwargs.get('title', '')}
            Description: {kwargs.get('description', '')}
            Price: {kwargs.get('price', '')}
            Location: {kwargs.get('location', '')}
            Category: {kwargs.get('category', '')}
            
            Use the WordPress interaction tool to create the post.
            Ensure all required information is provided.
            """,
            agent=agents['product_agent'],
            expected_output="Confirmation of successful product posting"
        )
    
    elif task_type == "register":
        return Task(
            description=f"""
            Register a new user with the following information:
            Username: {kwargs.get('username', '')}
            Email: {kwargs.get('email', '')}
            Password: {kwargs.get('password', '')}
            
            Use the WordPress interaction tool to create the user account.
            Validate the information and provide appropriate feedback.
            """,
            agent=agents['user_agent'],
            expected_output="User registration confirmation and next steps"
        )
    
    elif task_type == "login":
        return Task(
            description=f"""
            Authenticate user login with:
            Username: {kwargs.get('username', '')}
            Password: {kwargs.get('password', '')}
            
            Use the WordPress interaction tool to authenticate.
            Provide appropriate success or error messages.
            """,
            agent=agents['user_agent'],
            expected_output="Login status and user dashboard access"
        )
    
    else:
        return Task(
            description=f"""
            Handle general request: {kwargs.get('request', '')}
            
            Analyze the request and provide appropriate assistance.
            Route to specific functionality if needed.
            """,
            agent=agents['voice_agent'],
            expected_output="Helpful response to user request"
        )