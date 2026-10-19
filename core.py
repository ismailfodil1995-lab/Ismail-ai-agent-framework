import os
import pkgutil
import importlib.util

class TargetedSkillRegistry:
    def __init__(self):
        self.skills = []
        self.load_target_skills()
        self.display_dashboard()

    def load_target_skills(self):
        """Read the defined skills and directories specifically for skills and tools"""
        
        # Define the required base files directly without randomness
        target_files = [
            "lead_agent_core.py",
            "n8n_bridge.py",
            "bot.py",
            "brain.py",
            "api_manager.py",
            "decision_engine.py",
            "executor.py"
        ]
        
        # Check the "tools" directory if it exists to extract everything inside it
        tools_dir = "tools"
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith(".py") and not file.startswith("_"):
                    target_files.append(os.path.join(tools_dir, file))

        # Load and process only the required files
        for path in target_files:
            if os.path.exists(path):
                file_name = os.path.basename(path)
                skill_id = file_name[:-3]
                skill_name = skill_id.replace("_", " ").title()
                description = f"Active component in the path: {path}"

                try:
                    spec = importlib.util.spec_from_file_location(skill_id, path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "SKILL_NAME"):
                        skill_name = module.SKILL_NAME
                    if hasattr(module, "DESCRIPTION"):
                        description = module.DESCRIPTION
                except Exception:
                    pass

                # Avoid duplicates
                if not any(s['id'] == skill_id for s in self.skills):
                    self.skills.append({
                        "name": skill_name,
                        "id": skill_id,
                        "path": path,
                        "description": description
                    })