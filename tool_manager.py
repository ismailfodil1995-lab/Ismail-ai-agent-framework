from tools import run_tool

try:
    from plugins.registry import execute as execute_plugin
except ImportError:
    execute_plugin = None


class ToolManager:
    """
    إدارة وتشغيل الأدوات والـ Plugins
    """

    def execute(self, command: str):
        if not command or not str(command).strip():
            return None

        clean_command = str(command).strip()

        # 1. تشغيل الأدوات المحلية أولاً (Tools)
        try:
            result = run_tool(clean_command)
            if result is not None:
                return result
        except Exception as e:
            print(f"[Tool Error] Failure executing '{clean_command}': {e}")

        # 2. تشغيل الـ Plugins إن وجدت
        if execute_plugin:
            try:
                result = execute_plugin(clean_command)
                if result is not None:
                    return result
            except Exception as e:
                print(f"[Plugin Error] Failure executing '{clean_command}': {e}")

        return None

    def has_tool(self, command: str) -> bool:
        return True


# ==========================================
# إنشاء الـ Instance الموحد للمشروع
# ==========================================
tool_manager = ToolManager()