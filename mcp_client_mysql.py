import asyncio
import json
import requests
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from pathlib import Path

server_path = Path(__file__).resolve().with_name("mcp_server_mysql.py")
print("MCP server file:", server_path)

server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(server_path)]
)

OLLAMA_URL = "http://localhost:15000/api/chat"
MODEL = "gemma3:12b"


def call_ollama(messages, json_mode=False):

    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    if json_mode:
        body["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=body
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


async def main():

    # --------------------------------
    # MCP Server Launch Configuration
    # --------------------------------

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # --------------------------------
            # List Available MCP Tools
            # --------------------------------

            tools = await session.list_tools()

            print("=== MCP Tools ===")

            for tool in tools.tools:
                print("-", tool.name)

            print()

            # --------------------------------
            # User Question
            # --------------------------------

            user_question = input("Question: ")

            # --------------------------------
            # Gemma Determines the Tool and Parameters
            # --------------------------------

            decision_prompt = f"""
You are an ERP assistant.

The following tool is available.

Tool name:
get_product_stock

Function:
Look up the product name, current stock quantity,
and price using the product code.

Input parameter:
product_code: string

Analyze the user's question and determine
whether this tool is needed.

If the tool is needed, respond only in the following JSON format:

{{
  "tool": "get_product_stock",
  "arguments": {{
    "product_code": "PRODUCT_CODE"
  }}
}}

If the tool is not needed:

{{
  "tool": null
}}

User question:

{user_question}
"""

            decision = call_ollama(
                [
                    {
                        "role": "user",
                        "content": decision_prompt
                    }
                ],
                json_mode=True
            )

            print("\n=== Gemma Decision ===")
            print(decision)

            try:
                command = json.loads(decision)

            except json.JSONDecodeError as e:

                print("JSON parsing error:", e)
                return

            # --------------------------------
            # Handle Questions That Do Not Require a Tool
            # --------------------------------

            if command.get("tool") is None:

                answer = call_ollama(
                    [
                        {
                            "role": "user",
                            "content": user_question
                        }
                    ]
                )

                print("\n=== Final Answer ===")
                print(answer)

                return

            # --------------------------------
            # Call the MCP Tool
            # --------------------------------

            tool_name = command["tool"]
            arguments = command["arguments"]
            # tool_name = "get_product_stock"
            # arguments = {"product_code": "B200"}

            print("\n=== MCP Tool Call ===")
            print("Tool:", tool_name)
            print("Arguments:", arguments)

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            # --------------------------------
            # Convert the MCP Result to a String
            # --------------------------------

            tool_result = ""

            for item in result.content:

                if hasattr(item, "text"):
                    tool_result += item.text

            print("\n=== MCP Result ===")
            print(tool_result)

            # --------------------------------
            # Gemma Generates the Final Natural Language Answer
            # --------------------------------

            final_prompt = f"""
User question:

{user_question}

ERP system query result:

{tool_result}

Using only the ERP query result above,
provide a brief and natural answer to the user's question in English.

Do not invent information that was not returned by the query.
"""

            answer = call_ollama(
                [
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ]
            )

            print("\n=== Final Answer ===")
            print(answer)


if __name__ == "__main__":

    asyncio.run(main())