# Simple LangChain Agent Example
# Demonstrates the core concept with minimal code

from langchain.agents import AgentType, initialize_agent, Tool
from langchain.llms import FakeListLLM

# Define two simple tools
def greet_tool(name: str) -> str:
    """Simple greeting tool"""
    return f"Hello, {name}! Nice to meet you."

def add_tool(query: str) -> str:
    """Simple addition tool - expects format 'a+b'"""
    try:
        # Very basic parsing for demonstration
        if '+' in query:
            parts = query.split('+')
            a = float(parts[0].strip())
            b = float(parts[1].strip())
            return str(a + b)
        else:
            return "Please use format: 'number+number' (e.g., '5+3')"
    except:
        return "Error in calculation. Please use format: 'number+number'"

# Create Tool objects
greeting = Tool(
    name="Greeting",
    func=greet_tool,
    description="Greets a person. Input should be a name."
)

adder = Tool(
    name="Adder",
    func=add_tool,
    description="Adds two numbers. Input should be in format 'a+b' (e.g., '5+3')."
)

tools = [greeting, adder]

# Use a fake LLM for demonstration (no API key needed)
# This LLM will return predefined responses to show the agent working
responses = [
    # First response: decide to use the greeting tool
    'Thought: The user said hello and wants to be greeted. I should use the greeting tool.\nAction: Greeting\nAction Input: "Alice"',

    # Second response: after greeting, decide to do math
    'Thought: The user also asked a math question. I should use the adder tool.\nAction: Adder\nAction Input: "5+3"',

    # Third response: combine results
    'Thought: I have greeted the user and calculated the sum. Now I can provide a complete response.\nFinal Answer: Hello Alice! Nice to meet you. The answer to 5+3 is 8.'
]

llm = FakeListLLM(responses=responses)

# Initialize the agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True  # This shows the agent's thinking process
)

# Run the agent
if __name__ == "__main__":
    print("=== Simple LangChain Agent Demo ===\n")
    print("Asking: 'Hello Alice, what is 5+3?'\n")

    response = agent.run("Hello Alice, what is 5+3?")
    print(f"\nFinal Response:\n{response}")