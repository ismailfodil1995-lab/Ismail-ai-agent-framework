import os
import hashlib
import asyncio
import threading
from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

from llm.manager import generate
from computer_tools import read_pdf


class PDFAI:
    """
    محرك RAG حقيقي لمعالجة وتحليل ملفات PDF.
    يعتمد على تقطيع ذكي RecursiveCharacterTextSplitter وقاعدة ChromaDB
    مع نموذج Embeddings خفيف ومجاني (all-MiniLM-L6-v2) لاسترجاع Top-K بدقة.
    """

    CHUNK_SIZE_DEFAULT: int = 1000
    CHUNK_OVERLAP_DEFAULT: int = 200

    def __init__(self, chunk_size: int = CHUNK_SIZE_DEFAULT, chunk_overlap: int = CHUNK_OVERLAP_DEFAULT):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.client = chromadb.Client()
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self._indexed_cache: dict = {}
        self._lock = threading.Lock()   # حماية cache عند تعدد الخيوط

    def _get_collection_name(self, filename: str) -> str:
        file_hash = hashlib.md5(os.path.abspath(filename).encode("utf-8")).hexdigest()
        return f"pdf_rag_{file_hash[:16]}"

    def _index_document(self, filename: str) -> Optional[chromadb.Collection]:
        if not filename or not os.path.exists(filename):
            return None

        mtime = os.path.getmtime(filename)
        col_name = self._get_collection_name(filename)

        # القراءة خارج Lock (لا تتعارض مع الكتابة)
        with self._lock:
            if self._indexed_cache.get(filename) == mtime:
                return self.client.get_collection(name=col_name, embedding_function=self.embedding_fn)

        raw_text = read_pdf(filename)
        if not raw_text or raw_text.startswith("PDF not found") or raw_text.startswith("Error"):
            return None

        chunks = self.splitter.split_text(raw_text)
        if not chunks:
            return None

        with self._lock:
            try:
                self.client.delete_collection(name=col_name)
            except Exception:
                pass

            collection = self.client.create_collection(
                name=col_name,
                embedding_function=self.embedding_fn
            )

            ids = [f"c_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename, "chunk_id": i} for i in range(len(chunks))]

            collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )

            self._indexed_cache[filename] = mtime

        return collection

    async def aindex_document(self, filename: str) -> Optional[chromadb.Collection]:
        return await asyncio.to_thread(self._index_document, filename)

    async def ask_async(self, filename: str, question: str, top_k: int = 4) -> str:
        if not filename or not os.path.exists(filename):
            return f"Error: PDF file '{filename}' not found."
        if not question or not str(question).strip():
            return "Error: No question provided."

        collection = await self.aindex_document(filename)
        if not collection:
            return "Error: Could not extract or index content from PDF."

        def _retrieve():
            count = collection.count()
            k = min(top_k, count) if count > 0 else 1
            res = collection.query(query_texts=[question], n_results=k)
            return res.get("documents", [[]])[0]

        retrieved_chunks = await asyncio.to_thread(_retrieve)
        if not retrieved_chunks:
            return "لم يتم العثور على سياق ذي صلة داخل المستند."

        context = "\n\n---\n\n".join(retrieved_chunks)
        prompt = f"""أنت مساعد ذكي ومحلل مستندات محترف. أجب عن سؤال المستخدم بدقة استناداً فقط إلى السياق المسترجع أدناه عبر نظام الـ RAG.
إذا لم تجد الإجابة بشكل واضح في السياق، اذكر ذلك بأمانة.

[سياق الـ RAG المسترجع (Top-{len(retrieved_chunks)})]:
{context}

[السؤال]:
{question}

[الإجابة الشاملة بالعربية]:"""

        return await asyncio.to_thread(generate, prompt)

    def ask(self, filename: str, question: str, top_k: int = 4) -> str:
        """واجهة متزامنة للتوافق مع أدوات النظام وأطر الاستدعاء المباشرة"""
        collection = self._index_document(filename)
        if not collection:
            return f"Error: Cannot index or read '{filename}'."

        count = collection.count()
        k = min(top_k, count) if count > 0 else 1
        res = collection.query(query_texts=[question], n_results=k)
        retrieved_chunks = res.get("documents", [[]])[0]

        if not retrieved_chunks:
            return "لم يتم العثور على سياق ذي صلة داخل المستند."

        context = "\n\n---\n\n".join(retrieved_chunks)
        prompt = f"""أنت مساعد ذكي ومحلل مستندات محترف. أجب عن سؤال المستخدم بدقة استناداً فقط إلى السياق المسترجع أدناه عبر نظام الـ RAG.
إذا لم تجد الإجابة بشكل واضح في السياق، اذكر ذلك بأمانة.

[سياق الـ RAG المسترجع (Top-{len(retrieved_chunks)})]:
{context}

[السؤال]:
{question}

[الإجابة الشاملة بالعربية]:"""

        return generate(prompt)

    async def summarize_async(self, filename: str) -> str:
        if not filename or not os.path.exists(filename):
            return f"Error: PDF file '{filename}' not found."

        raw_text = await asyncio.to_thread(read_pdf, filename)
        if not raw_text or raw_text.startswith("PDF not found") or raw_text.startswith("Error"):
            return "Error: Could not read PDF content."

        chunks = self.splitter.split_text(raw_text)
        if len(chunks) <= 3:
            content_to_summarize = raw_text
        else:
            collection = await self.aindex_document(filename)
            queries = [
                "نظرة عامة والهدف الرئيسي والمقدمة",
                "أهم القرارات والنتائج والتوصيات التنفيذية",
                "الأرقام والإحصائيات والتواريخ الهامة"
            ]

            def _get_salient_chunks():
                selected = []
                for q in queries:
                    res = collection.query(query_texts=[q], n_results=2)
                    for doc in res.get("documents", [[]])[0]:
                        if doc not in selected:
                            selected.append(doc)
                return "\n\n---\n\n".join(selected)

            content_to_summarize = await asyncio.to_thread(_get_salient_chunks)

        prompt = f"""أنت محلل وثائق تنفيذي. استناداً إلى المحتوى المستخرج من المستند أدناه، أعد ملخصاً مهنياً شاملاً:

1. نظرة عامة موجزة (3-4 أسطر).
2. أهم النقاط والقرارات الرئيسية.
3. التواريخ والأرقام والأسماء البارزة.

[المحتوى المستخرج]:
{content_to_summarize}

[التقرير الملخص بالعربية]:"""

        return await asyncio.to_thread(generate, prompt)

    def summarize(self, filename: str) -> str:
        """واجهة متزامنة للتوافق الكامل"""
        raw_text = read_pdf(filename)
        if not raw_text or raw_text.startswith("PDF not found") or raw_text.startswith("Error"):
            return "Error: Could not read PDF content."

        chunks = self.splitter.split_text(raw_text)
        if len(chunks) <= 3:
            content_to_summarize = raw_text
        else:
            collection = self._index_document(filename)
            queries = ["الهدف الرئيسي", "أهم النتائج والتوصيات", "الأرقام والتواريخ"]
            selected = []
            for q in queries:
                res = collection.query(query_texts=[q], n_results=2)
                for doc in res.get("documents", [[]])[0]:
                    if doc not in selected:
                        selected.append(doc)
            content_to_summarize = "\n\n---\n\n".join(selected)

        prompt = f"""أنت محلل وثائق تنفيذي. أعد ملخصاً مهنياً دقيقاً بالعربية استناداً إلى المحتوى التالي:

1. نظرة عامة موجزة.
2. أهم النقاط والقرارات.
3. الأرقام والأسماء البارزة.

[المحتوى]:
{content_to_summarize}

[التقرير الملخص]:"""

        return generate(prompt)


# النسخة العامة الجاهزة للاستدعاء الفوري
pdf_ai = PDFAI()
