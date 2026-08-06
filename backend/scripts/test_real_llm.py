import asyncio
import os
import sys

# Ensure backend src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm import get_llm
from src.agents.tools.search_test_drive_options.tool import search_test_drive_options

async def test_llm():
    try:
        llm = get_llm()
        print(f"Using LLM: {llm.model_name}")
        print(f"Base URL: {getattr(llm, 'base_url', None)}")
        
        # Bind the search_test_drive_options tool
        llm_with_tools = llm.bind_tools([search_test_drive_options])
        
        print("Sending request: 'Tôi muốn lái thử xe VF3 ở Hà Nội'...")
        response = await llm_with_tools.ainvoke("Tôi muốn lái thử xe VF3 ở Hà Nội. Hãy gọi tool để tìm showroom.")
        
        print("\n--- LLM Response ---")
        print(f"Content: {response.content}")
        print(f"Tool calls: {response.tool_calls}")
        print("--------------------")
        
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(test_llm())
