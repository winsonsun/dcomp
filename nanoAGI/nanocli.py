#!/usr/bin/env python3
"""
nanocli.py: The Top-Level Agentic Orchestrator for NanoAGI.
This CLI wraps the dynamic cognitive engine. It parses user requests,
feeds them into the Orchestrator DAG (Intent, Router, Firewall, Metacognition),
and safely executes the workflow.
"""
import sys
import argparse
from runtime.orchestrator import build_orchestrator_dag

def print_header():
    print("=" * 50)
    print("   NanoAGI Orchestrator: Active and Listening   ")
    print("=" * 50)

def interactive_mode(execute_dag):
    """Starts a REPL session for continuous interaction."""
    print_header()
    print("Type 'exit' or 'quit' to stop.\n")
    while True:
        try:
            user_input = input("User> ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue
            
            response = execute_dag(user_input)
            print(f"\n[NanoAGI] {response}\n")
            
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"\n[System Error] Unexpected failure: {e}\n")

def single_shot_mode(execute_dag, prompt: str):
    """Executes a single prompt through the DAG and exits."""
    print_header()
    print(f"[Input Received]: {prompt}\n")
    
    try:
        response = execute_dag(prompt)
        print(f"\n[NanoAGI] {response}\n")
    except Exception as e:
        print(f"\n[System Error] Unexpected failure: {e}\n")

def main():
    parser = argparse.ArgumentParser(description="NanoAGI Agentic Orchestrator")
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Command: ask (Single-shot)
    p_ask = subparsers.add_parser("ask", help="Send a single prompt to the orchestrator.")
    p_ask.add_argument("prompt", help="The user prompt to execute.")

    # Command: chat (Interactive)
    p_chat = subparsers.add_parser("chat", help="Start an interactive chat session.")

    args = parser.parse_args()

    # Initialize the core orchestrator pipeline
    execute_dag = build_orchestrator_dag()

    if args.mode == "ask":
        single_shot_mode(execute_dag, args.prompt)
    elif args.mode == "chat":
        interactive_mode(execute_dag)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
