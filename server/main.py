import asyncio
import os
import time
import config
import utils
import state_manager
from droidrun import AdbTools
from llama_index.llms.ollama import Ollama

os.environ["GOOGLE_API_KEY"] = "fake"
os.environ["OPENAI_API_KEY"] = "fake"

# --- GLOBAL STATE ---
current_app_start_time = 0
last_package = ""
current_app_name = "Waiting..."
last_verdict = "SAFE"
dashboard_logs = [] 

# --- INTERNAL STATE ---
last_screen_content_hash = "" 
landscape_checked = False 

def log(message):
    print(message)
    dashboard_logs.append(message)
    if len(dashboard_logs) > 100:
        dashboard_logs.pop(0)

async def punish(tools):
    """Executes the user-defined punishment"""
    if config.PUNISHMENT_TYPE == "BACK":
        # Press Back Button
        await tools.press_key(4)
    
    elif config.PUNISHMENT_TYPE == "OPEN_APP" and config.PUNISHMENT_TARGET:
        # Force open a productive app (e.g., Duolingo)
        # Note: DroidRun start_app usually needs activity, but try launch intent first
        print(f"🔨 PUNISHMENT: Opening {config.PUNISHMENT_TARGET}")
        await tools.start_app(config.PUNISHMENT_TARGET)
        
    else:
        # Default: Press Home (Key 3)
        await tools.press_key(3) 

async def main():
    global current_app_start_time, last_package 
    global landscape_checked, last_screen_content_hash, last_verdict, current_app_name
    
    log(f"🚀 SYSTEM INITIALIZED | {config.USER_PERSONA}")
    
    qwen_llm = Ollama(model="qwen2.5", request_timeout=30.0, base_url="http://localhost:11434")
    tools = AdbTools()
    
    loop_delay = 2.0 

    while config.IS_RUNNING:
        try:
            # 1. GET RAW STATE
            raw_state = await tools.get_state()
            package, app_name = utils.get_app_info(raw_state)
            current_app_name = app_name if app_name else package

            # --- APP SWITCH & PENALTY RESET ---
            if package != last_package:
                log(f"👉 App Switch: {current_app_name}")
                landscape_checked = False 
                last_screen_content_hash = "" 
                last_verdict = "SAFE"
                current_app_start_time = time.time()
                last_package = package

            # --- WHITELIST CHECK ---
            if package in config.WHITELIST_APPS:
                await asyncio.sleep(2.0)
                continue

            # =======================================================
            # 🛑 PHASE 1: HARD LIMITS & PENALTIES
            # =======================================================
            
            # Update Usage
            state_manager.USAGE_CACHE[package] = state_manager.USAGE_CACHE.get(package, 0) + loop_delay

            # A. HARD BLOCK / TIME LIMIT
            rule = state_manager.CONFIG_CACHE.get(package)
            if rule:
                if rule["blocked"]:
                    log(f"🚫 BLOCKED: {package}")
                    await punish(tools)
                    continue
                if state_manager.USAGE_CACHE[package] >= rule["limit"]:
                    log(f"⏰ LIMIT REACHED: {package}")
                    await punish(tools)
                    continue

            # B. GRACE PERIOD (With Penalty Logic)
            # If in Penalty Box, Grace Period = 0. Otherwise, use Config.
            current_grace = 0 if state_manager.is_penalized(package) else config.GRACE_PERIOD
            
            if (time.time() - current_app_start_time) < current_grace:
                # We skip content checks during grace, BUT NOT if it's a browser (too risky)
                if "chrome" not in package and "browser" not in package:
                    await asyncio.sleep(1.0) 
                    continue

            # =======================================================
            # 🧠 PHASE 2: CONTENT ANALYSIS (App & Browser)
            # =======================================================
            text_list, is_currently_landscape = utils.process_state(raw_state)
            current_content_str = "".join(text_list)

            # --- LOGIC GATE 1: BROWSER SNEAKING ---
            if "chrome" in package or "browser" in package:
                is_bad, reason = utils.is_browser_distraction(text_list)
                if is_bad:
                    log(f"🚨 BROWSER KILL: {reason}")
                    state_manager.add_strike(package)
                    # USE CONFIG VARIABLE HERE
                    state_manager.set_penalty(package, config.PENALTY_DURATION) 
                    await punish(tools)
                    continue

            # --- LOGIC GATE 2: DOOMSCROLLING ---
            if config.DOOMSCROLL_MODE or config.STUDY_MODE:
                if "youtube" in package:
                    safe, reason, is_shorts = utils.is_youtube_safe(text_list)
                    if is_shorts:
                        log(f"🚨 KILL: {reason}")
                        state_manager.add_strike(package)
                        # USE CONFIG VARIABLE HERE
                        state_manager.set_penalty(package, config.PENALTY_DURATION)
                        await punish(tools)
                        continue

                if "instagram" in package:
                    if not utils.is_insta_safe(text_list):
                        log("🚨 KILL: Insta Feed")
                        state_manager.add_strike(package)
                        state_manager.set_penalty(package, 120)
                        await punish(tools)
                        continue

            # --- LOGIC GATE 2: DEEP FOCUS (LLM Content Check) ---
            # Active ONLY if Study Mode is ON
            if config.STUDY_MODE and ("youtube" in package):
                
                content_to_analyze = ""
                
                # A. Handle Landscape Mode (The "Tap" Logic)
                if is_currently_landscape and not landscape_checked:
                    log("👀 Landscape detected. Tapping to reveal title...")
                    # Tap center of screen to wake up UI overlays
                    await tools.swipe(1200, 500, 1200, 500, 50)
                    await asyncio.sleep(1.0) # Wait for UI to fade in
                    
                    # Re-scan state
                    new_state = await tools.get_state()
                    new_texts, _ = utils.process_state(new_state)
                    content_to_analyze = utils.clean_for_llm(new_texts)
                    
                    landscape_checked = True # Don't tap again until app switch or major change
                    last_screen_content_hash = "".join(new_texts)

                # B. Handle Portrait Mode
                elif not is_currently_landscape:
                    content_to_analyze = utils.clean_for_llm(text_list)
                    landscape_checked = False # Reset flag if we go back to portrait
                
                # C. Skip if screen is static (Optimization)
                elif current_content_str == last_screen_content_hash:
                    # Enforce previous verdict if it was bad
                    if "DISTRACTION" in last_verdict:
                         await punish(tools)
                    await asyncio.sleep(loop_delay)
                    continue

                # D. LLM Check
                if len(content_to_analyze) < 10: 
                    # If we still can't find text, skip to avoid wasting tokens
                    await asyncio.sleep(loop_delay)
                    continue

                log(f"🤔 Analyzing: {content_to_analyze[:40]}...")
                
                prompt = (
                    f"User Persona: {config.USER_PERSONA}\n"
                    f"User Focus: {config.USER_CURRENT_FOCUS}\n"
                    f"Video Title: {content_to_analyze}\n"
                    "Ignore the Content that seems like sponsered advertisement classify apart from these\n"
                    "Task: Classify as RELEVANT or DISTRACTION. Reply with one word only."
                )
                
                try:
                    response = await qwen_llm.acomplete(prompt)
                    verdict = response.text.strip().upper()
                    last_verdict = verdict 
                    log(f"🤖 Verdict: {verdict}")

                    if "DISTRACTION" in verdict:
                        log("🚨 Distraction Found!")
                        state_manager.add_strike(package)
                        state_manager.set_penalty(package, 300)
                        await punish(tools)
                        
                    # Update Hash
                    last_screen_content_hash = current_content_str
                    
                except Exception as llm_err:
                    log(f"⚠️ LLM Error: {llm_err}")

            await asyncio.sleep(loop_delay)

        except Exception as e:
            log(f"❌ Error: {e}")
            await asyncio.sleep(5)
            
    log("🛑 SYSTEM STOPPED")

if __name__ == "__main__":
    config.IS_RUNNING = True
    asyncio.run(main())