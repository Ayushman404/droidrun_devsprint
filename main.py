import asyncio
import os
import time
import config
import utils
from droidrun import AdbTools
from llama_index.llms.ollama import Ollama

# Fake Keys
os.environ["GOOGLE_API_KEY"] = "fake"
os.environ["OPENAI_API_KEY"] = "fake"

# --- STATE ---
app_history = {} 
current_app_start_time = 0
last_package = ""

# --- LANDSCAPE STATE ---
was_landscape = False
landscape_checked = False # Ensures we only tap once per session

async def main():
    global app_history, current_app_start_time, last_package 
    global was_landscape, landscape_checked
    
    print(f"🔥 TAP & SNAP ENFORCER | Persona: {config.USER_PERSONA}")
    print("------------------------------------------------")

    qwen_llm = Ollama(model="qwen2.5", request_timeout=30.0, base_url="http://localhost:11434")
    tools = AdbTools()

    while True:
        try:
            # 1. GET DATA
            raw_state = await tools.get_state()
            package, app_name = utils.get_app_info(raw_state)
            
            # --- A. WHITELIST ---
            if package in config.WHITELIST_APPS or "launcher" in package:
                if last_package and last_package not in config.WHITELIST_APPS:
                    app_history[last_package] = time.time()
                last_package = package
                was_landscape = False # Reset landscape memory
                landscape_checked = False
                await asyncio.sleep(5)
                continue

            # --- B. GRACE PERIOD ---
            if package != last_package:
                print(f"👉 Opened: {app_name}")
                landscape_checked = False # Reset checking logic
                last_closed = app_history.get(package, 0)
                if (time.time() - last_closed) < config.REOPEN_PENALTY_TIME:
                    print(f"🚫 ANTI-CHEAT: Instant Check.")
                    current_app_start_time = 0 
                else:
                    current_app_start_time = time.time()
                last_package = package

            if (time.time() - current_app_start_time) < config.GRACE_PERIOD:
                await asyncio.sleep(5)
                continue

            # 2. EXTRACTION
            text_list = utils.extract_all_text(raw_state)
            is_currently_landscape = utils.is_landscape(raw_state)

            # 3. TECHNICAL CHECKS
            if "instagram" in package and not utils.is_insta_safe(text_list):
                print("🚨 RULE BROKEN: Insta Feed/Reels.")
                await punish(tools)
                continue

            if "youtube" in package:
                safe, reason, is_shorts = utils.is_youtube_safe(text_list, state=raw_state)
                if is_shorts:
                    print(f"🚨 Shorts Detected: {reason}")
                    await punish(tools)
                    continue

                # 4. LANDSCAPE TAP & SNAP LOGIC
                if config.STUDY_MODE:
                    
                    content_to_analyze = ""
                    source = ""

                    # CASE A: Just entered Landscape (or need to re-check)
                    if is_currently_landscape and not landscape_checked:
                        print("👀 Landscape Detected. Tapping to reveal title...")
                        
                        # TAP THE SCREEN (Center-ish coordinates)
                        # Assuming 1080x2400 resolution roughly. 
                        # In landscape, center is approx X=1200, Y=500
                        await tools.swipe(1200, 500, 1200, 500, 50) 
                        
                        # WAIT for UI to fade in
                        await asyncio.sleep(1.5) 
                        
                        # RE-CAPTURE STATE (Now with title visible)
                        new_state = await tools.get_state()
                        new_text_list = utils.extract_all_text(new_state)
                        
                        # CLEAN DATA
                        cleaned_text = utils.clean_for_llm(new_text_list)
                        content_to_analyze = cleaned_text
                        source = "Landscape Tap"
                        landscape_checked = True # Mark done so we don't tap again
                        
                    # CASE B: Portrait Mode (Text is always visible)
                    elif not is_currently_landscape:
                        content_to_analyze = utils.clean_for_llm(text_list)
                        source = "Portrait Mode"
                        landscape_checked = False # Reset if we go back to portrait
                    
                    # CASE C: Already checked Landscape
                    else:
                        # We are in landscape, and we already checked it.
                        # Do nothing to save battery/annoyance.
                        await asyncio.sleep(5)
                        continue

                    # --- VERDICT PHASE ---
                    # If we have content (from Tap or Portrait), verify it
                    if len(content_to_analyze) < 10:
                        print("⚠️ No readable text found. Skipping.")
                        continue

                    # Log what we are sending
                    try:
                        with open("llm_input_log.txt", "w", encoding="utf-8") as f:
                            f.write(content_to_analyze)
                    except: pass

                    print(f"🤔 Checking ({source}): {content_to_analyze[:40]}...")

                    prompt = (
                        f"User Persona: {config.USER_PERSONA}\n"
                        f"Current Focus: {config.USER_CURRENT_FOCUS}\n"
                        f"Video Title: {content_to_analyze}\n\n"
                        "TASK: Classify this video content.\n"
                        "1. RELEVANT: Educational, Coding, Math, Science, Tech News, Tutorials.\n"
                        "2. DISTRACTION: Movies, Gaming, Music Videos, Vlogs, Pranks, Entertainment.\n"
                        "Reply ONLY with the word 'RELEVANT' or 'DISTRACTION'."
                    )

                    response = await qwen_llm.acomplete(prompt)
                    verdict = response.text.strip().upper()
                    print(f"🤖 Verdict: {verdict}")

                    if "DISTRACTION" in verdict:
                        print(f"🚨 Distraction Found!")
                        await punish(tools)
                    else:
                        print("✅ Safe.")

            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(5)

async def punish(tools):
    print("💥 PUNISHMENT EXECUTED!")
    await tools.press_key(3) 

if __name__ == "__main__":
    asyncio.run(main())