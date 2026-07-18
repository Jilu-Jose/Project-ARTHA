#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error
import getpass
import os

def print_banner():
    r = "\033[91m"  # Red
    w = "\033[97m"  # White
    rst = "\033[0m" # Reset
    
    banner = f"""
{r}    _    {w}  ____  {r} _____ {w} _   _ {r}    _    
{r}   / \\   {w} |  _ \\ {r}|_   _|{w}| | | |{r}   / \\   
{r}  / _ \\  {w} | |_) |{r}  | |  {w}| |_| |{r}  / _ \\  
{r} / ___ \\ {w} |  _ < {r}  | |  {w}|  _  |{r} / ___ \\ 
{r}/_/   \\_\\{w} |_| \\_\\{r}  |_|  {w}|_| |_|{r}/_/   \\_\\ {rst}
    """
    print(banner)
    print(f"{w}Welcome to A.R.T.H.A CLI Chatbot{rst}\n")

def login(base_url):
    print("Please login to continue.")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    
    data = json.dumps({"email": email, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return res_data.get('access_token')
    except urllib.error.HTTPError as e:
        print(f"\n\033[91mError logging in: {e.read().decode()}\033[0m")
        return None
    except urllib.error.URLError as e:
        print(f"\n\033[91mFailed to connect to backend at {base_url}. Ensure the server is running.\033[0m")
        sys.exit(1)

def chat_loop(base_url, token):
    print("\nType 'exit' or 'quit' to close the chat.")
    conversation_id = None
    
    while True:
        try:
            question = input("\n\033[94mYou:\033[0m ")
            if question.lower() in ['exit', 'quit']:
                break
            if not question.strip():
                continue
                
            payload = {
                "question": question,
                "stream": False,
                "domain_filters": []
            }
            if conversation_id:
                payload["conversation_id"] = conversation_id
                
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(f"{base_url}/ask", data=data, headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            })
            
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode())
                answer = res_data.get('answer', '')
                conversation_id = res_data.get('conversation_id')
                citations = res_data.get('citations', [])
                
                print(f"\n\033[92mA.R.T.H.A:\033[0m {answer}")
                if citations:
                    print("\n\033[93mCitations:\033[0m")
                    for idx, c in enumerate(citations, 1):
                        print(f"  [{idx}] {c.get('act_name')} - {c.get('section')} (Confidence: {c.get('confidence', 0):.2f})")
                        
        except urllib.error.HTTPError as e:
            print(f"\033[91mAPI Error: {e.read().decode()}\033[0m")
        except urllib.error.URLError as e:
            print(f"\033[91mConnection Error: {e}\033[0m")
        except KeyboardInterrupt:
            break

def main():
    # Enable colors for windows terminal if needed
    if os.name == 'nt':
        os.system('color')
        
    print_banner()
    base_url = "http://localhost:8000"
    
    token = login(base_url)
    if not token:
        sys.exit(1)
        
    print("\n\033[92mLogin successful!\033[0m")
    chat_loop(base_url, token)

if __name__ == "__main__":
    main()
