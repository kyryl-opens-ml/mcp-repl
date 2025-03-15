from anthropic import Anthropic


class LLMClient:
    """Handles interactions with the LLM"""

    def __init__(self):
        self.anthropic = Anthropic()
        self.chat_history = []

    async def add_user_message(self, query: str):
        """Add a user message to the chat history"""
        self.chat_history.append({"role": "user", "content": query})

    async def get_llm_response(self, available_tools=None):
        """Get a response from the LLM based on the current chat history"""
        system_prompt = """You are Claude, an AI assistant by Anthropic. You can help with a wide range of tasks including:
1. Writing and explaining code in various programming languages
2. Answering general knowledge questions
3. Providing creative content like stories or poems
4. Using the available tools when appropriate

When asked to write code or perform general tasks unrelated to the available tools, you should do so directly. Only use the provided tools when they are specifically relevant to the user's request."""

        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=self.chat_history,
            tools=available_tools if available_tools else [],
            max_tokens=1000,
        )

        return response

    async def add_assistant_message(self, content):
        """Add an assistant message to the chat history"""
        assistant_message = {"role": "assistant", "content": content}
        self.chat_history.append(assistant_message)
        return assistant_message

    async def add_tool_result(self, tool_use_id, result):
        """Add a tool result to the chat history"""
        tool_result_message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result.content,
                }
            ],
        }
        self.chat_history.append(tool_result_message)
