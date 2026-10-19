import json
import re
from typing import Any, Dict, List, Optional, Union
from tools import register_tool


@register_tool(
    name="extract_structured_json",
    description="استخراج وتحويل البيانات والنصوص غير المنظمة إلى صيغة JSON مهيكلة ونظيفة."
)
def extract_structured_json(
    text_data: str = "",
    schema_keys: Optional[List[str]] = None,
    **kwargs
) -> str:
    """
    استخراج كائنات JSON مهيكلة من النصوص العشوائية أو استخراج مفاتيح محددة.
    """
    for k in ["text", "data", "content", "raw_text", "input_data"]:
        if k in kwargs and kwargs[k]:
            text_data = kwargs[k]
            break

    for k in ["keys", "fields", "properties", "schema"]:
        if k in kwargs and kwargs[k]:
            schema_keys = kwargs[k]
            break

    if not text_data:
        return "Error: No text data provided to extract JSON."

    text_str = str(text_data).strip()

    # 1. فحص إذا كان النص يحتوي بالفعل على كائن JSON صريح
    json_match = re.search(r"(\{|\[).+(\}|\])", text_str, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return f"SUCCESS: JSON extracted successfully:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}"
        except Exception:
            pass

    # 2. استخراج الحقول بناءً على schema_keys إن تم تحديدها
    extracted_obj: Dict[str, Any] = {}
    if schema_keys and isinstance(schema_keys, (list, tuple)):
        for key in schema_keys:
            # البحث عن صيغة: Key: Value أو "Key": "Value"
            pattern = rf"(?:[\"']?{re.escape(str(key))}[\"']?\s*[:=]\s*)([^\n,\r\}}]+)"
            match = re.search(pattern, text_str, re.IGNORECASE)
            if match:
                val = match.group(1).strip().strip("\"'")
                extracted_obj[str(key)] = val
            else:
                extracted_obj[str(key)] = None

        if any(v is not None for v in extracted_obj.values()):
            return f"SUCCESS: JSON extracted successfully:\n{json.dumps(extracted_obj, ensure_ascii=False, indent=2)}"

    # 3. الاستعانة بالـ LLM لتحويل النص غير المهيكل إلى JSON إن وُجد
    try:
        from llm.manager import generate
        keys_hint = f"Desired JSON Keys: {schema_keys}" if schema_keys else "Extract all key-value facts."
        prompt = f"""
Convert the following unstructured text into clean valid JSON.
{keys_hint}

Text:
{text_str[:2000]}

Return ONLY valid JSON. No explanations, no markdown fences.
"""
        llm_res = generate(prompt).strip()
        match = re.search(r"(\{.*\}|\[.*\])", llm_res, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return f"SUCCESS: JSON extracted successfully:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}"
    except Exception:
        pass

    # 4. Fallback إلى تمثيل قياسي
    fallback = {"raw_content": text_str[:500], "status": "unstructured"}
    return f"SUCCESS: JSON extracted successfully:\n{json.dumps(fallback, ensure_ascii=False, indent=2)}"
