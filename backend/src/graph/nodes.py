import json
import os
import logging
import re
from typing import Dict, Any

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.messages import SystemMessage, HumanMessage

from backend.src.graph.state import VideoAuditState, ComplianceIssue
from backend.src.services.video_indexer import VideoIndexerService

logger = logging.getLogger("brand-guardian")


def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    video_url = state.get("video_url")
    video_id = state.get("video_id", "vid_demo")
    local_filename = "temp_audit_video.mp4"

    logger.info(f"[Indexer] Processing: {video_url}")

    try:
        vi_service = VideoIndexerService()

        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise ValueError("Only YouTube URLs are supported.")

        azure_video_id = vi_service.upload_video(local_path, video_name=video_id)
        logger.info(f"[Indexer] Upload success. Azure ID: {azure_video_id}")

        if os.path.exists(local_path):
            os.remove(local_path)

        raw_insights = vi_service.wait_for_processing(azure_video_id)
        clean_data = vi_service.extract_data(raw_insights)

        logger.info("[Indexer] Extraction complete.")
        return clean_data

    except Exception as e:
        logger.error(f"[Indexer] Failed: {e}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": []
        }


def audit_content_node(state: VideoAuditState) -> Dict[str, Any]:
    logger.info("[Auditor] Querying knowledge base and LLM.")

    transcript = state.get("transcript", "")
    if not transcript:
        logger.warning("[Auditor] No transcript available. Skipping audit.")
        return {
            "final_status": "FAIL",
            "final_report": "Audit skipped: video processing failed (no transcript)."
        }

    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )

    ocr_text = state.get("ocr_text", [])
    query_text = f"{transcript} {' '.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    retrieved_rules = "\n\n".join([doc.page_content for doc in docs])

    system_prompt = f"""You are a Senior Brand Compliance Auditor.

OFFICIAL REGULATORY RULES:
{retrieved_rules}

INSTRUCTIONS:
1. Analyze the transcript and OCR text provided.
2. Identify ANY violations of the rules above.
3. Respond ONLY with valid JSON in this exact format:

{{
    "compliance_results": [
        {{
            "category": "Claim Validation",
            "severity": "CRITICAL",
            "description": "Description of the violation."
        }}
    ],
    "status": "FAIL",
    "final_report": "Summary of findings."
}}

If no violations are found, set "status" to "PASS" and "compliance_results" to [].
"""

    user_message = f"""VIDEO METADATA: {state.get('video_metadata', {})}
TRANSCRIPT: {transcript}
ON-SCREEN TEXT (OCR): {ocr_text}
"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        content = response.content
        if "```" in content:
            match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1)

        audit_data = json.loads(content.strip())

        return {
            "compliance_results": audit_data.get("compliance_results", []),
            "final_status": audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report", "No report generated.")
        }

    except Exception as e:
        logger.error(f"[Auditor] Failed: {str(e)}")
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "final_report": "Audit failed due to a system error."
        }