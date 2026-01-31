import config
import re

def process_state(state):
    """
    SUPER OPTIMIZATION:
    Extracts Text, IDs, AND Landscape Info in a SINGLE pass.
    Returns: (text_list, is_landscape_bool)
    """
    texts = []
    max_width = 0
    max_height = 0

    # 1. Get the UI List (Index 2)
    ui_list = []
    if isinstance(state, tuple) and len(state) > 2:
        ui_list = state[2]
    elif isinstance(state, list):
        ui_list = state

    if not isinstance(ui_list, list):
        return [], False

    # 2. FAST LANDSCAPE CHECK (O(1) - Just check the Root Node)
    # The first item is ALWAYS the root container (Full Screen). 
    # We don't need to scan the whole tree for dimensions.
    if len(ui_list) > 0:
        root = ui_list[0]
        if isinstance(root, dict) and "bounds" in root:
            try:
                # Parse "0,0,1080,2400"
                coords = [int(x) for x in root["bounds"].split(',')]
                max_width = coords[2] - coords[0]
                max_height = coords[3] - coords[1]
            except: pass

    # 3. TEXT EXTRACTION (Iterative - Faster than Recursion)
    # We use a stack to avoid recursion limit and function call overhead
    stack = list(ui_list)
    while stack:
        node = stack.pop()
        if not isinstance(node, dict): continue

        # A. Grab Text
        txt = node.get("text")
        if txt: texts.append(str(txt))
        
        # B. Grab Content Description
        cd = node.get("content_description")
        if cd: texts.append(str(cd))
        
        # C. Grab Critical IDs (for Shorts)
        rid = node.get("resourceId")
        if rid and "reel" in str(rid):
            texts.append(str(rid))

        # D. Add children to stack
        children = node.get("children")
        if children and isinstance(children, list):
            stack.extend(children)

    # 4. Determine Orientation
    is_landscape = False
    if max_width > 0 and max_height > 0:
        is_landscape = max_width > max_height

    return texts, is_landscape

def get_app_info(state):
    """O(1) Lookup for Package Name"""
    try:
        if isinstance(state, tuple) and len(state) > 0:
            meta = state[-1]
            if isinstance(meta, dict):
                return meta.get("packageName", ""), meta.get("currentApp", "")
    except: pass
    return "", ""

def is_insta_safe(text_list):
    dm_indicators = ["Type a message", "Message...", "Active now", "Voice message"]
    screen_text = " ".join(text_list)
    for keyword in dm_indicators:
        if keyword in screen_text:
            return True 
    return False

def is_youtube_safe(text_list):
    screen_text = " ".join(text_list)
    # Strict ID Check
    if "reel_recycler" in screen_text or "reel_player" in screen_text:
        return False, "Shorts Player Detected", True
    return True, "Safe", False

def clean_for_llm(text_list):
    clean_lines = []
    for line in text_list:
        if "com." in line or "android." in line or "resourceId" in line: continue
        if re.search(r'\d+:\d+', line): continue
        if line in ["more_vert", "Search", "Close", "Minimize", "Cast"]: continue
        clean_lines.append(line)
    return " | ".join(clean_lines)