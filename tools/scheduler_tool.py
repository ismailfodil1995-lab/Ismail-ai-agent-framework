"""
Scheduler Tool – tools/scheduler_tool.py
أداة مستقلة لجدولة المهام وتشغيلها تلقائياً في وقت محدد.
مفصولة عن brain.py لضمان النظافة المعمارية وسهولة الصيانة.
"""

TOOL_PARAMETERS = {
    "schedule_task": {
        "type": "object",
        "properties": {
            "task_name": {"type": "string", "description": "اسم المهمة المجدولة"},
            "run_time": {"type": "string", "description": "وقت التشغيل اليومي بصيغة HH:MM مثل 08:00"}
        }
    }
}


def schedule_task(task_name: str = "daily_routine", run_time: str = "08:00", **kwargs) -> str:
    """جدولة وتشغيل المهام تلقائياً في وقت محدد يومياً دون حظر النظام."""
    for k in ["task", "name", "job"]:
        if k in kwargs and kwargs[k]:
            task_name = kwargs[k]
            break
    for k in ["time", "run_time", "at"]:
        if k in kwargs and kwargs[k]:
            run_time = kwargs[k]
            break
    try:
        import schedule
        schedule.every().day.at(run_time).do(
            lambda: print(f"⏰ [Scheduler] Executing: {task_name}")
        )
        return f"SUCCESS: Task '{task_name}' scheduled daily at {run_time}."
    except Exception as e:
        return f"Error scheduling task: {str(e)}"


# سجل الأدوات المُصدَّرة من هذا الموديول
EXPORTED_TOOLS = {
    "schedule_task": {
        "name": "Automated Task Scheduler",
        "description": "جدولة المهام والأوامر للتشغيل التلقائي في وقت محدد يومياً.",
        "parameters": TOOL_PARAMETERS["schedule_task"],
        "fn": schedule_task,
        "function": schedule_task
    }
}
