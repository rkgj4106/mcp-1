import asyncio
import json
import requests
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ========================================
# Ollama URL on the GPU Server
# ========================================

OLLAMA_URL = "http://localhost:15000/api/chat"

MODEL = "gemma3:12b"


def call_ollama(messages):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


async def main():

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # --------------------------------
            # Check Tools Provided by the MCP Server
            # --------------------------------

            tools = await session.list_tools()

            print("=== MCP Tools ===")

            for tool in tools.tools:
                print(tool.name)

            print()

            # --------------------------------
            # User Question
            # --------------------------------

            user_question = input("Question: ")

            # --------------------------------
            # Ask Gemma to Decide Which Tool to Use
            # --------------------------------

            prompt = f"""
You are an ERP assistant.

Available tool:

get_product_stock(product_code)

Function:
Look up the product name, stock quantity,
and price using the product code.

Analyze the user's question.

If the tool is needed, respond only in the following JSON format:

{{
  "tool": "get_product_stock",
  "arguments": {{
    "product_code": "PRODUCT_CODE"
  }}
}}

If the tool is not needed, respond with:

{{
  "tool": null
}}

User question:

{user_question}
"""

            decision = call_ollama([
                {
                    "role": "user",
                    "content": prompt
                }
            ])

            print("\n=== Gemma Decision ===")
            print(decision)

            try:
                command = json.loads(decision)

            except json.JSONDecodeError:

                print("Gemma did not return valid JSON.")
                return

            # --------------------------------
            # Call the MCP Tool
            # --------------------------------

            if command["tool"] == "get_product_stock":

                arguments = command["arguments"]

                result = await session.call_tool(
                    "get_product_stock",
                    arguments=arguments
                )

                print("\n=== MCP Result ===")
                print(result)

                # Convert the MCP result to text
                tool_result = ""

                for item in result.content:

                    if hasattr(item, "text"):
                        tool_result += item.text

                # --------------------------------
                # Send the Result to Gemma
                # --------------------------------

                final_prompt = f"""
User question:

{user_question}

ERP query result:

{tool_result}

Using the ERP data above,
provide a brief and natural answer in English.
"""

                answer = call_ollama([
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ])

                print("\n=== Final Answer ===")
                print(answer)

            else:

                answer = call_ollama([
                    {
                        "role": "user",
                        "content": user_question
                    }
                ])

                print("\n=== Final Answer ===")
                print(answer)


if __name__ == "__main__":

    asyncio.run(main())