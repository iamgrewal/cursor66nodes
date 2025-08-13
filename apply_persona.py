import os
import json
import re
import requests
import shutil

# --- Constants ---
PROJECT_CONFIG_PATH = "project_config.md"
PERSONA_CONFIG_PATH = "persona.mcp.json"
RULES_DIR = ".cursor/rules"
RULES_BASE_URL = "https://raw.githubusercontent.com/iamgrewal/cursor66nodes/main/rulescursor/.cursor/rules"

# --- Helper Functions ---

def get_persona_from_config():
    """
    Reads the persona from the project_config.md file.
    The persona is expected to be between the STATIC:PERSONA markers.
    """
    try:
        with open(PROJECT_CONFIG_PATH, "r") as f:
            content = f.read()

        # Use regex to find the content between the markers
        match = re.search(r"<!-- STATIC:PERSONA:START -->(.*?)<!-- STATIC:PERSONA:END -->", content, re.DOTALL)
        if not match:
            print("❌ Error: Persona markers not found in project_config.md")
            return None

        # Extract the persona name, stripping whitespace and the ## Persona heading
        persona_content = match.group(1).strip()
        persona_name = persona_content.replace("## Persona", "").strip()

        if not persona_name:
            print("❌ Error: Persona name is empty in project_config.md")
            return None

        return persona_name

    except FileNotFoundError:
        print(f"❌ Error: {PROJECT_CONFIG_PATH} not found.")
        return None
    except Exception as e:
        print(f"❌ Error reading persona from config: {e}")
        return None

def get_persona_definitions():
    """
    Loads the persona definitions from the persona.mcp.json file.
    """
    try:
        with open(PERSONA_CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {PERSONA_CONFIG_PATH} not found.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {PERSONA_CONFIG_PATH}.")
        return None
    except Exception as e:
        print(f"❌ Error reading persona definitions: {e}")
        return None

def resolve_rules(persona_name, personas_data):
    """
    Resolves the full list of rules for a given persona, handling inheritance.
    """
    if not personas_data or "personas" not in personas_data:
        print("❌ Error: Invalid persona data format.")
        return set()

    all_personas = personas_data["personas"]

    if persona_name not in all_personas:
        print(f"❌ Error: Persona '{persona_name}' not found in {PERSONA_CONFIG_PATH}.")
        return set()

    persona = all_personas[persona_name]
    rules = set(persona.get("rules", []))

    # Handle inheritance recursively
    if "inherits" in persona:
        parent_persona_name = persona["inherits"]
        parent_rules = resolve_rules(parent_persona_name, personas_data)
        rules.update(parent_rules)

    return rules

def download_rule(rule_path):
    """
    Downloads a single rule file from the GitHub repository.
    """
    url = f"{RULES_BASE_URL}/{rule_path}"
    target_file = os.path.join(RULES_DIR, rule_path)

    try:
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        # Download the file
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(target_file, "w") as f:
            f.write(response.text)

        print(f"  ✅ Downloaded: {rule_path}")

    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Warning: Failed to download {rule_path} (Error: {e})")
    except Exception as e:
        print(f"  ❌ Error processing {rule_path}: {e}")


# --- Main Execution ---

def main():
    """
    Main function to apply the persona-based rules.
    """
    print("🚀 Starting Persona-based Rule Application...")

    # 1. Get the active persona
    persona_name = get_persona_from_config()
    if not persona_name:
        return
    print(f"👤 Active Persona: {persona_name}")

    # 2. Get persona definitions
    personas_data = get_persona_definitions()
    if not personas_data:
        return

    # 3. Resolve the full list of rules
    rules_to_apply = resolve_rules(persona_name, personas_data)
    if not rules_to_apply:
        print("No rules to apply. Exiting.")
        return

    print(f" Found {len(rules_to_apply)} rules to apply for persona '{persona_name}'.")

    # 4. Clean the rules directory
    if os.path.exists(RULES_DIR):
        print(f"🧹 Cleaning existing rules directory: {RULES_DIR}")
        try:
            shutil.rmtree(RULES_DIR)
        except Exception as e:
            print(f"❌ Error cleaning directory: {e}")
            return

    os.makedirs(RULES_DIR)
    print("📦 Downloading new rules...")

    # 5. Download and apply each rule
    for rule in sorted(list(rules_to_apply)):
        download_rule(rule)

    print("\n🎉 Persona rules applied successfully!")


if __name__ == "__main__":
    main()
