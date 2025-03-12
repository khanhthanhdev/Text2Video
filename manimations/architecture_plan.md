# AI Agent Architecture Plan

## 1. Frameworks and Tools
- **Python**: The primary programming language.
- **Manim**: For creating mathematical animations.
- **OpenAI API**: For generating Manim code from text prompts.
- **pydantic-ai**: For structured AI agent creation, function calling, and workflow management.
- **Gradio**: For creating a user interface to input prompts and display generated videos.
- **dotenv**: For managing environment variables.
- **Logging**: For logging information and errors.

## 2. Agent Architecture
- **Input Handling**: Use Gradio to create a user interface where users can input text prompts.
- **Agent Structure**: Leverage pydantic-ai to define the agent's schema, capabilities, and functions.
- **System Prompts**: Use both static and dynamic system prompts to guide the agent's behavior.
  - Static prompts: Define the agent's role and general capabilities
  - Dynamic prompts: Adjust behavior based on complexity settings and current context
- **Keyword Identification**: Use pydantic-ai with OpenAI API to identify keywords and generate Manim code.
- **Scenario Creation**: Define structured schemas in pydantic-ai to guide the generation of scenarios.
- **Function Search**: Use pydantic-ai's function calling capabilities to organize and call Manim functions.
- **Code Generation and Testing**: The generated code will be tested by rendering the video using Manim.

## 3. Workflow
1. **User Input**: The user inputs a text prompt describing a mathematical or physics concept.
2. **Agent Processing**: The pydantic-ai agent processes the input through defined schemas and tools.
   - System prompts dynamically adjust based on user requirements
   - Tools are applied in sequence using the agent's capabilities
3. **Keyword Identification and Scenario Creation**: The agent uses OpenAI API to analyze the prompt and generate a structured scenario.
4. **Code Generation**: The agent transforms the structured scenario into Manim code using defined tools.
5. **Video Rendering**: The code is executed using Manim to render the video.
6. **Output**: The generated video is displayed to the user.

## 4. Detailed Steps
1. **Setup Environment**:
   - Ensure all required packages are installed (`gradio`, `openai`, `pydantic-ai`, `dotenv`, `manim`, etc.).
   - Set up environment variables in `.env` file (e.g., `TOGETHER_API_KEY`).
   - Configure pydantic-ai with appropriate model settings.

2. **Create Agent Structure**:
   - Define pydantic models for input prompts, scenario descriptions, and animation parameters.
   - Create static and dynamic system prompts to guide agent behavior:
     - Static: Define the agent's role and general capabilities
     - Dynamic: Adjust behavior based on request complexity and context
   - Create tool functions for scenario extraction, code generation, and rendering.
   - Configure the agent with appropriate tools and models.

3. **Create User Interface**:
   - Use Gradio to create a web interface for inputting prompts and displaying results.
   - Add complexity selection controls to customize animation generation.
   - Connect the UI to the pydantic-ai agent.

4. **Generate Manim Code**:
   - Implement functions using pydantic-ai tools to transform user prompts into structured scenarios.
   - Convert structured scenarios into Manim code templates.
   - Fill templates with specifics from the scenario.

5. **Render Video**:
   - Implement a function to render the generated Manim code into a video.
   - Add error handling and validation using pydantic models.

6. **Display Results**:
   - Display the generated video and code in the Gradio interface.
   - Provide feedback and explanations based on the agent's processing steps.