import asyncio
import os
import time
import config
import utils
from droidrun import AdbTools
from llama_index.llms.ollama import Ollama

os.environ["GOOGLE_API_KEY"] = "fake"
os.environ["OPENAI_API_KEY"] = "fake"

# --- STATE ---
app_history = {} 
current_app_start_time = 0
last_package = ""

# --- CACHE ---
last_screen_content_hash = "" 
last_verdict = "SAFE"         

# --- LANDSCAPE STATE ---
landscape_checked = False 

async def main():
    global app_history, current_app_start_time, last_package 
    global landscape_checked, last_screen_content_hash, last_verdict
    
    print(f"⚡ HIGH-PERFORMANCE ENFORCER | Persona: {config.USER_PERSONA}")
    print("------------------------------------------------")

    qwen_llm = Ollama(model="qwen2.5", request_timeout=30.0, base_url="http://localhost:11434")
    tools = AdbTools()

    loop_delay = 2.0 

    while True:
        try:
            # 1. GET RAW STATE
            raw_state = await tools.get_state()
            package, app_name = utils.get_app_info(raw_state)
            
            # =======================================================
            # 🛑 APP SWITCH & HISTORY TRACKER
            # =======================================================
            if package != last_package:
                print(f"👉 Opened: {app_name}")
                
                # 1. Record when we LEFT the previous app
                if last_package:
                    app_history[last_package] = time.time()
                
                # 2. Reset Session
                landscape_checked = False 
                last_screen_content_hash = "" 
                last_verdict = "SAFE"
                current_app_start_time = time.time() # Default reset
                
                # 3. ANTI-CHEAT (Only for Non-Whitelist Apps)
                # FIX: Don't punish user for opening Home Screen "too fast"
                is_whitelisted = package in config.WHITELIST_APPS or "launcher" in package
                
                if not is_whitelisted:
                    last_closed = app_history.get(package, 0)
                    time_since_closed = time.time() - last_closed
                    
                    if time_since_closed < config.REOPEN_PENALTY_TIME:
                        print(f"🚫 ANTI-CHEAT: Reopened in {int(time_since_closed)}s. Instant Check.")
                        current_app_start_time = 0 
                
                last_package = package

            # =======================================================
            # A. WHITELIST CHECK (Home Screen Immunity)
            # =======================================================
            if package in config.WHITELIST_APPS or "launcher" in package:
                loop_delay = 3.0 
                await asyncio.sleep(loop_delay)
                continue

            # =======================================================
            # B. GRACE PERIOD
            # =======================================================
            if (time.time() - current_app_start_time) < config.GRACE_PERIOD:
                await asyncio.sleep(1.0) 
                continue

            # =======================================================
            # C. SINGLE-PASS EXTRACTION
            # =======================================================
            text_list, is_currently_landscape = utils.process_state(raw_state)

            # =======================================================
            # D. FAST LANE (Technical Checks)
            # =======================================================
            
            if "youtube" in package:
                loop_delay = 0.5 
                safe, reason, is_shorts = utils.is_youtube_safe(text_list)
                if is_shorts:
                    print(f"🚨 INSTANT KILL: {reason}")
                    await punish(tools)
                    continue 
            else:
                loop_delay = 2.0 

            if "instagram" in package:
                if not utils.is_insta_safe(text_list):
                    print("🚨 INSTANT KILL: Insta Feed/Reels.")
                    await punish(tools)
                    continue 

            # =======================================================
            # E. SMART LANE (Hash & LLM)
            # =======================================================
            
            # Hash Check
            current_content_str = "".join(text_list)
            if current_content_str == last_screen_content_hash:
                if "DISTRACTION" in last_verdict:
                    await punish(tools)
                await asyncio.sleep(loop_delay) 
                continue
            
            last_screen_content_hash = current_content_str

            # LLM Check
            if config.STUDY_MODE and "youtube" in package:
                
                content_to_analyze = ""
                source = ""

                # Landscape Tap
                if is_currently_landscape and not landscape_checked:
                    print("👀 Landscape Switch. Tapping...")
                    await tools.swipe(1200, 500, 1200, 500, 50) 
                    await asyncio.sleep(1.5) 
                    
                    new_state = await tools.get_state()
                    new_texts, _ = utils.process_state(new_state)
                    content_to_analyze = utils.clean_for_llm(new_texts)
                    
                    source = "Landscape Tap"
                    landscape_checked = True 
                    last_screen_content_hash = "".join(new_texts)

                # Portrait
                elif not is_currently_landscape:
                    content_to_analyze = utils.clean_for_llm(text_list)
                    source = "Portrait Mode"
                    landscape_checked = False 
                
                else:
                    await asyncio.sleep(loop_delay)
                    continue

                if len(content_to_analyze) < 10:
                    continue

                print(f"🤔 Checking ({source}): {content_to_analyze[:40]}...")

                prompt = (
                    f"User: {config.USER_PERSONA}\n"
                    f"Focus: {config.USER_CURRENT_FOCUS}\n"
                    f"Title: {content_to_analyze}\n"
                    "Ignore content that seems like advertisements.\n"
                    "Classify as RELEVANT or DISTRACTION. Reply one word."
                )
                print(prompt)

                response = await qwen_llm.acomplete(prompt)
                verdict = response.text.strip().upper()
                last_verdict = verdict 
                
                print(f"🤖 Verdict: {verdict}")

                if "DISTRACTION" in verdict:
                    print(f"🚨 Distraction Found!")
                    await punish(tools)

            await asyncio.sleep(loop_delay)

        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(5)

async def punish(tools):
    print("💥 PUNISHMENT!")
    await tools.press_key(3) 

if __name__ == "__main__":
    asyncio.run(main())