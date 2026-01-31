import config
import re

# --- 1. DATA CLEANING ---
def clean_for_llm(text_list):
    """
    Removes technical garbage (com.google..., time stamps, resource IDs)
    Returns a clean string of just the Title and Channel Name.
    """
    clean_lines = []
    
    for line in text_list:
        # Ignore package names and IDs
        if "com." in line or "android." in line or "resourceId" in line:
            continue
        # Ignore time stamps like "0:00 / 10:00"
        if re.search(r'\d+:\d+', line):
            continue
        # Ignore tiny generic buttons
        if line in ["more_vert", "Search", "Close", "Minimize", "Cast", "Autoplay"]:
            continue
            
        clean_lines.append(line)
    
    return " | ".join(clean_lines)

# --- 2. DATA EXTRACTOR ---
def extract_all_text(data):
    texts = []
    if isinstance(data, tuple) and len(data) > 2:
        if isinstance(data[2], list):
            texts.extend(extract_all_text(data[2]))
            
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ["text", "content_description", "text_content"] and value:
                texts.append(str(value))
            # Critical: Keep technical IDs visible for Shorts detection
            elif key == "resourceId" and "reel" in str(value):
                texts.append(str(value))
            else:
                texts.extend(extract_all_text(value))
                
    elif isinstance(data, list) or isinstance(data, tuple):
        for item in data:
            texts.extend(extract_all_text(item))
            
    return texts

def get_app_info(state):
    if isinstance(state, tuple):
        for item in state:
            if isinstance(item, dict) and "packageName" in item:
                return item.get("packageName", ""), item.get("currentApp", "")
    elif isinstance(state, dict):
        return state.get("packageName", ""), state.get("currentApp", "")
    return "", ""

def is_landscape(state):
    """
    Determines orientation by parsing the 'bounds' of the root UI element.
    Format: "x1,y1,x2,y2" (e.g., "0,0,2400,1080")
    """
    max_width = 0
    max_height = 0

    def parse_bounds(bounds_str):
        try:
            # Parse "0,0,2400,1080" -> [0, 0, 2400, 1080]
            coords = [int(x) for x in bounds_str.split(',')]
            return coords[2] - coords[0], coords[3] - coords[1] # w, h
        except:
            return 0, 0

    def find_largest_bounds(data):
        nonlocal max_width, max_height
        
        # Check current dict for bounds
        if isinstance(data, dict) and "bounds" in data:
            w, h = parse_bounds(data["bounds"])
            if w > max_width: max_width = w
            if h > max_height: max_height = h
        
        # Recurse into children
        if isinstance(data, dict):
            for key, value in data.items():
                find_largest_bounds(value)
        elif isinstance(data, list) or isinstance(data, tuple):
            for item in data:
                find_largest_bounds(item)

    # 1. Scan the whole state tree
    find_largest_bounds(state)

    # 2. Compare Dimensions
    if max_width > 0 and max_height > 0:
        # If Width > Height, it is Landscape
        return max_width > max_height
        
    return False

# --- 3. CONTEXT INTELLIGENCE ---

def is_insta_safe(text_list):
    dm_indicators = ["Type a message", "Message...", "Active now", "Voice message"]
    screen_text = " ".join(text_list)
    for keyword in dm_indicators:
        if keyword in screen_text:
            return True 
    return False

def is_youtube_safe(text_list, state=None):
    screen_text = " ".join(text_list)
    
    try:
        with open("youtube_text.txt", "w", encoding="utf-8") as f:
            f.write(screen_text)
    except: pass
    
    # --- STRICT SHORTS CHECK ---
    # Only block if we see the actual player container or recycler.
    # We ignore 'reel_time_bar' to avoid false positives in the feed.
    if "reel_recycler" in screen_text or "reel_player" in screen_text:
        return False, "Shorts Player Detected (Strict ID Check)", True

    return True, "Safe", False