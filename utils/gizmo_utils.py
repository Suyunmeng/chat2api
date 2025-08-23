"""
Gizmo-related utility functions
For handling GPTs model name parsing and mapping
"""

from typing import Optional, Tuple


def parse_gizmo_model(model_name: str) -> Tuple[Optional[str], str]:
    """
    Parse model name to extract Gizmo ID and base model information
    
    Args:
        model_name: Original model name
        
    Returns:
        Tuple[gizmo_id, base_model_hint]: (Gizmo ID, base model hint)
    """
    if not model_name:
        return None, ""
    
    model_lower = model_name.lower()
    
    # Check if it's a Gizmo model
    if "gizmo" not in model_lower and "g-" not in model_lower:
        return None, ""
    
    gizmo_id = None
    base_model_hint = ""
    
    # Extract Gizmo ID
    if "gizmo-g-" in model_lower:
        # Format: gpt-4-gizmo-g-xxxxx
        gizmo_id = "g-" + model_name.split("gizmo-g-")[-1]
        base_model_hint = model_name.split("-gizmo-g-")[0]
    elif "g-" in model_lower:
        # Format: g-xxxxx or other-g-xxxxx
        gizmo_id = "g-" + model_name.split("g-")[-1]
        if "-g-" in model_lower:
            base_model_hint = model_name.split("-g-")[0]
        else:
            base_model_hint = "gpt-4o"  # default
    
    return gizmo_id, base_model_hint


def get_optimal_base_model(base_model_hint: str, user_persona: str = None) -> str:
    """
    Get optimal base model based on model hint and user type
    
    Args:
        base_model_hint: Base model hint extracted from model name
        user_persona: User type (chatgpt-paid, chatgpt-free, etc.)
        
    Returns:
        Optimal base model name
    """
    is_paid_user = user_persona == "chatgpt-paid"
    hint_lower = base_model_hint.lower()
    
    # O4 series
    if "o4-mini-high" in hint_lower:
        return "o4-mini-high"
    elif "o4-mini-medium" in hint_lower:
        return "o4-mini-medium" 
    elif "o4-mini-low" in hint_lower:
        return "o4-mini-low"
    elif "o4-mini" in hint_lower:
        return "o4-mini"
    
    # O3 series
    elif "o3-mini-high" in hint_lower:
        return "o3-mini-high"
    elif "o3-mini-medium" in hint_lower:
        return "o3-mini-medium" 
    elif "o3-mini-low" in hint_lower:
        return "o3-mini-low"
    elif "o3-mini" in hint_lower:
        return "o3-mini"
    elif "o3" in hint_lower:
        return "o3"
    
    # O1 series
    elif "o1-preview" in hint_lower:
        return "o1-preview" if is_paid_user else "gpt-4o"
    elif "o1-pro" in hint_lower:
        return "o1-pro" if is_paid_user else "gpt-4o"
    elif "o1-mini" in hint_lower:
        return "o1-mini"
    elif "o1" in hint_lower:
        return "o1" if is_paid_user else "gpt-4o"
    
    # GPT-5 series
    elif "gpt-5" in hint_lower:
        return "gpt-5" if is_paid_user else "gpt-4o"
    
    # GPT-4 series
    elif "gpt-4.5o" in hint_lower:
        return "gpt-4.5o"
    elif "gpt-4-5" in hint_lower:
        return "gpt-4-5"
    elif "gpt-4o-canmore" in hint_lower:
        return "gpt-4o-canmore"
    elif "gpt-4o-mini" in hint_lower:
        return "gpt-4o-mini"
    elif "gpt-4o" in hint_lower:
        return "gpt-4o"
    elif "gpt-4-mobile" in hint_lower:
        return "gpt-4-mobile"
    elif "gpt-4-turbo" in hint_lower:
        return "gpt-4-turbo" if is_paid_user else "gpt-4o"
    elif "gpt-4" in hint_lower:
        # Key optimization: Avoid consuming GPT-4 quota for regular users calling GPTs
        return "gpt-4" if is_paid_user else "gpt-4o"
    
    # GPT-3.5 series
    elif "gpt-3.5" in hint_lower:
        return "text-davinci-002-render-sha"
    
    # Auto mode
    elif "auto" in hint_lower:
        return "auto"
    
    # Default case: Use gpt-4o (user-friendly for regular users)
    else:
        return "gpt-4o"


def is_gizmo_model(model_name: str) -> bool:
    """
    Check if model name is a Gizmo model
    
    Args:
        model_name: Model name
        
    Returns:
        Whether it's a Gizmo model
    """
    if not model_name:
        return False
    
    model_lower = model_name.lower()
    return "gizmo" in model_lower or "g-" in model_lower
