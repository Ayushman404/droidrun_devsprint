import asyncio
import os
import json
from droidrun import DroidAgent, AdbTools
from llama_index.llms.ollama import Ollama

# Keys setup
os.environ["GOOGLE_API_KEY"] = "fake"
os.environ["OPENAI_API_KEY"] = "fake"

# --- HELPER: Recursively find all text in JSON ---
def extract_all_text(data):
    texts = []
    if isinstance(data, dict):
        for key, value in data.items():
            # Agar key 'text', 'content_desc', ya 'resource_id' hai to value le lo
            if key in ["text", "content_description", "text_content"] and value:
                texts.append(str(value))
            else:
                texts.extend(extract_all_text(value))
    elif isinstance(data, list) or isinstance(data, tuple):
        for item in data:
            texts.extend(extract_all_text(item))
    return texts


import re

def clean_noise(text_list):
    clean_items = []
    
    for item in text_list:
        item = str(item).strip()
        
        # 1. Skip empty strings
        if not item: continue
        
        # 2. THE BIG FIX: Remove anything starting with "com." or "android."
        # This kills 90% of the noise instantly.
        if item.startswith("com.") or item.startswith("android."):
            continue
            
        # 3. Skip numbers/stats (optional, but "4628 likes" doesn't prove doomscrolling)
        # If it's just a number like "10" or "@2131977409", skip it
        # if item.isdigit() or item.startswith("@"):
        #     continue

        # 4. Filter generic UI words that appear everywhere
        # if item in ["More", "Back", "Close", "Share", "Like", "Comment", "Send", "Double tap to play or pause."]:
        #     continue

        # 5. Deduplicate consecutive items
        if clean_items and clean_items[-1] == item:
            continue
            
        clean_items.append(item)
        
    return " | ".join(clean_items)

async def main():
    print("🚀 Initializing...")

    # 1. SETUP LOCAL OLLAMA
    qwen_llm = Ollama(
        model="qwen2.5", 
        request_timeout=120.0,
        base_url="http://localhost:11434"
    )

    # 2. SETUP TOOLS
    tools_obj = AdbTools()

    # 3. SETUP AGENT
    agent = DroidAgent(
        goal="Check for doomscrolling",
        tools=tools_obj,
        llms=qwen_llm
    )

    print("👀 Reading FULL screen state...")
    
    # 4. GET RAW STATE
    raw_state = await tools_obj.get_state()
    
    # --- THE FIX: EXTRACT EVERYTHING ---
    # Tuple ho ya Dict, hum sab kuch pass karenge extractor ko
    all_text_list = extract_all_text(raw_state)
    
    # Join list into a single clean string
    clean_text = clean_noise(all_text_list)
    
    # 3. Save & Print
    with open("screen_dump.txt", "w", encoding="utf-8") as f:
        f.write(clean_text)
    
    
    # 5. ASK QWEN
    print("🤖 Analyzing...")
    prompt = (
        "Analyze this Android screen text. Does it contain keywords like 'Reels', 'Shorts', 'TikTok', "
        "or is the user watching a short video loop? "
        "Reply exactly with YES or NO.\n\n"
        f"Screen Text: {clean_text}"
    )
    
    response = await qwen_llm.acomplete(prompt)
    print(f"💡 Verdict: {response.text}")

if __name__ == "__main__":
    asyncio.run(main())