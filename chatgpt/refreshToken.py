import hashlib
import json
import random
import time

from fastapi import HTTPException

from utils.Client import Client
from utils.Logger import logger
from utils.configs import proxy_url_list
import utils.globals as globals


def save_token_list_to_file():
    """Save the current token_list to token.txt file
    
    This preserves all types of tokens in the list:
    - Refresh tokens (45 characters)
    - Access tokens (JWT format starting with 'eyJhbGciOi' or 'fk-')
    - Other token formats
    """
    try:
        with open(globals.TOKENS_FILE, "w", encoding="utf-8") as f:
            for token in globals.token_list:
                f.write(token + "\n")
        logger.info(f"Token list saved to file: {len(globals.token_list)} tokens")
    except Exception as e:
        logger.error(f"Failed to save token list to file: {e}")


def update_token_in_list(old_token, new_token):
    """Update a specific refresh token in the global token_list and save to file"""
    try:
        if old_token in globals.token_list:
            # Replace the old token with the new one
            index = globals.token_list.index(old_token)
            globals.token_list[index] = new_token
            logger.info(f"Updated refresh token in list: old={old_token[:10]}... -> new={new_token[:10]}...")
            
            # Save the updated list to file (preserves all token types)
            save_token_list_to_file()
            return True
        else:
            logger.warning(f"Refresh token not found in list for update: {old_token[:10]}...")
            return False
    except Exception as e:
        logger.error(f"Failed to update refresh token in list: {e}")
        return False


async def rt2ac(refresh_token, force_refresh=False):
    """
    Convert refresh_token to access_token
    Returns only access_token for backward compatibility
    """
    result = await rt2ac_with_new_rt(refresh_token, force_refresh)
    if isinstance(result, tuple):
        return result[0]  # Return only access_token
    return result


async def rt2ac_with_new_rt(refresh_token, force_refresh=False):
    """
    Convert refresh_token to access_token and return new refresh_token if updated
    Returns: access_token or (access_token, new_refresh_token)
    """
    if not force_refresh and (refresh_token in globals.refresh_map and int(time.time()) - globals.refresh_map.get(refresh_token, {}).get("timestamp", 0) < 5 * 24 * 60 * 60):
        access_token = globals.refresh_map[refresh_token]["token"]
        # logger.info(f"refresh_token -> access_token from cache")
        return access_token
    else:
        try:
            response_data = await chat_refresh(refresh_token)
            access_token = response_data.get('access_token')
            new_refresh_token = response_data.get('refresh_token', refresh_token)
            
            # Update cache with new access_token
            globals.refresh_map[refresh_token] = {"token": access_token, "timestamp": int(time.time())}
            
            # If we got a new refresh_token, update the mapping
            if new_refresh_token and new_refresh_token != refresh_token:
                # Remove old refresh_token mapping
                if refresh_token in globals.refresh_map:
                    del globals.refresh_map[refresh_token]
                # Add new refresh_token mapping
                globals.refresh_map[new_refresh_token] = {"token": access_token, "timestamp": int(time.time())}
                logger.info(f"Updated refresh_token mapping: old={refresh_token[:10]}... -> new={new_refresh_token[:10]}...")
                
                # Update token in the global token_list and file
                update_token_in_list(refresh_token, new_refresh_token)
            
            with open(globals.REFRESH_MAP_FILE, "w") as f:
                json.dump(globals.refresh_map, f, indent=4)
            logger.info(f"refresh_token -> access_token with openai: {access_token}")
            
            # Return tuple if refresh_token was updated, otherwise just access_token
            if new_refresh_token and new_refresh_token != refresh_token:
                return access_token, new_refresh_token
            else:
                return access_token
        except HTTPException as e:
            raise HTTPException(status_code=e.status_code, detail=e.detail)


async def chat_refresh(refresh_token):
    data = {
        "client_id": "app_WXrF1LSkiTtfYqiL6XtjygvX",  # Updated client ID
        "grant_type": "refresh_token",
        "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
        "refresh_token": refresh_token
    }
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://auth0.openai.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
    }
    session_id = hashlib.md5(refresh_token.encode()).hexdigest()
    proxy_url = random.choice(proxy_url_list).replace("{}", session_id) if proxy_url_list else None
    client = Client(proxy=proxy_url)
    try:
        r = await client.post("https://auth0.openai.com/oauth/token", json=data, headers=headers, timeout=15)
        if r.status_code == 200:
            response_data = r.json()
            return response_data  # Return complete response including new refresh_token
        else:
            if "invalid_grant" in r.text or "access_denied" in r.text:
                if refresh_token not in globals.error_token_list:
                    globals.error_token_list.append(refresh_token)
                    with open(globals.ERROR_TOKENS_FILE, "a", encoding="utf-8") as f:
                        f.write(refresh_token + "\n")
                raise Exception(r.text)
            else:
                raise Exception(r.text[:300])
    except Exception as e:
        logger.error(f"Failed to refresh access_token `{refresh_token}`: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh access_token.")
    finally:
        await client.close()
        del client
