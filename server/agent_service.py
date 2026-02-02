import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llama_index.llms.ollama import Ollama
from droidrun import DroidAgent
from droidrun.config_manager import DroidrunConfig

# --- CONFIGURATION ---
# Initialize the local LLM (Qwen 2.5)
# DroidAgent expects a dictionary of LLMs or a single LLM object
local_llm = Ollama(model="qwen2.5-coder:7b", request_timeout=120.0, base_url="http://localhost:11434")

# Initialize DroidRun Config (defaults are usually fine for local ADB)
droid_config = DroidrunConfig()

agent_router = APIRouter()

class TaskRequest(BaseModel):
    prompt: str 

@agent_router.post("/execute")
async def execute_local_task(req: TaskRequest):
    """
    Spins up a local DroidAgent to perform a task using Qwen 2.5.
    """
    print(f"🤖 AGENT ACTIVATING: {req.prompt}")
    
    try:
        # 1. Initialize the Agent
        # We pass the local_llm directly. 
        # reasoning=False is faster for simple tasks (CodeActAgent).
        # reasoning=True is better for complex planning (Manager -> Executor).
        agent = DroidAgent(
            goal=req.prompt + "Remember for this goal you can use droidrun packages like to directly opening apps without finding them in UI, also dont assume the index of any element in UI tree, only confirm from UI tree the index of element matching the required task to do then click it. Follow the droidrun different commands wherever you can use and follow their arguments syntax.",
            config=droid_config,
            llms=local_llm, # Passing our local Qwen instance
            # You can add custom_tools here if you need specific DB searches etc.
        )

        # 2. Run the Agent
        # This will take control of ADB, execute steps, and return.
        result = await agent.run()

        if result.success:
            return {
                "status": "success",
                "output": result.reason or "Task completed successfully.",
                # "history": [str(step) for step in result.history] # Optional: debug logs
            }
        else:
            return {
                "status": "failed",
                "output": result.error_message or "Unknown error occurred."
            }

    except Exception as e:
        print(f"❌ AGENT CRASH: {e}")
        raise HTTPException(status_code=500, detail=str(e))