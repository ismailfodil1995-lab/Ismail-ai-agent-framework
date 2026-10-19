class IntentClassifier:
    """
    مسؤول عن فهم نية المستخدم.
    """

    def __init__(self):

        self.pdf_commands = [

            "read pdf",
            "summarize pdf",
            "analyze pdf",
            "extract pdf"

        ]

        self.file_commands = [

            "create file",
            "read file",
            "write file",
            "append file",
            "delete file",
            "rename file",
            "list files"

        ]

        self.system_commands = [

            "time",
            "date",
            "hello",
            "hi",
            "مرحبا"

        ]

    # ======================================

    def detect(self, user_input):

        text = user_input.lower().strip()

        for cmd in self.system_commands:

            if text.startswith(cmd):

                return "system"

        for cmd in self.file_commands:

            if text.startswith(cmd):

                return "file"

        for cmd in self.pdf_commands:

            if text.startswith(cmd):

                return "pdf"

        return "chat"


intent_classifier = IntentClassifier()