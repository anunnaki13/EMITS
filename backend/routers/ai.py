# AI Intelligence Router with Conversation Memory
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import os
import json
import logging

from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import AIQueryRequest, AIQueryResponse, SmartBlendingRequest
from utils.database import db
from routers.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])
logger = logging.getLogger(__name__)

# ==================== CONVERSATION MEMORY ====================

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    module: Optional[str] = None

class ConversationSession(BaseModel):
    session_id: str
    user_id: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
    module: str = "general"

async def get_or_create_session(user_id: str, session_id: Optional[str] = None, module: str = "general") -> dict:
    """Get existing session or create new one"""
    if session_id:
        session = await db.ai_conversations.find_one({"session_id": session_id, "user_id": user_id}, {"_id": 0})
        if session:
            return session
    
    # Create new session
    new_session = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "module": module
    }
    await db.ai_conversations.insert_one(new_session)
    return new_session

async def add_message_to_session(session_id: str, role: str, content: str, module: str = None):
    """Add a message to conversation history"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": module
    }
    await db.ai_conversations.update_one(
        {"session_id": session_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )

async def get_conversation_context(session_id: str, max_messages: int = 10) -> str:
    """Get recent conversation history as context string"""
    session = await db.ai_conversations.find_one({"session_id": session_id}, {"_id": 0})
    if not session or not session.get("messages"):
        return ""
    
    recent_messages = session["messages"][-max_messages:]
    context_parts = []
    for msg in recent_messages:
        role_label = "Pengguna" if msg["role"] == "user" else "AI"
        context_parts.append(f"{role_label}: {msg['content']}")
    
    return "\n".join(context_parts)

# ==================== AI QUERY ENDPOINT ====================

class AIQueryWithSession(BaseModel):
    query: str
    module: str = "general"
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@router.post("/query")
async def ai_query(request: AIQueryWithSession, user: dict = Depends(get_current_user)):
    """AI Query with conversation memory support"""
    
    # Get or create session
    session = await get_or_create_session(user["id"], request.session_id, request.module)
    session_id = session["session_id"]
    
    # Get conversation context
    conversation_history = await get_conversation_context(session_id)
    
    # Get API key
    user_settings = await db.user_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    llm_key = None
    if user_settings and user_settings.get("custom_api_key"):
        llm_key = user_settings.get("custom_api_key")
    if not llm_key:
        llm_key = os.environ.get("EMERGENT_LLM_KEY")
    
    if not llm_key:
        raise HTTPException(status_code=400, detail="API Key tidak ditemukan")
    
    # Build system message based on module
    system_messages = {
        "general": "Anda adalah asisten AI untuk PLTU Tenayan yang membantu menganalisis data bahan bakar batubara.",
        "blending": "Anda adalah ahli optimasi blending batubara untuk PLTU Tenayan. Fokus pada analisis GCV, ash content, dan sulphur.",
        "boiler": "Anda adalah ahli analisis risiko boiler PLTU. Fokus pada deteksi slagging, fouling, dan korosi.",
        "contract": "Anda adalah ahli kontrak dan PO batubara. Fokus pada compliance, tracking pengiriman, dan analisis supplier.",
        "logistics": "Anda adalah ahli logistik batubara. Fokus pada efisiensi pengiriman, analisis losses, dan optimasi transportasi."
    }
    
    system_msg = system_messages.get(request.module, system_messages["general"])
    
    # Add conversation context to prompt
    full_prompt = request.query
    if conversation_history:
        full_prompt = f"""Riwayat Percakapan Sebelumnya:
{conversation_history}

Pertanyaan Terbaru: {request.query}

Jawab pertanyaan terbaru dengan mempertimbangkan konteks percakapan sebelumnya."""
    
    # Add message to session
    await add_message_to_session(session_id, "user", request.query, request.module)
    
    try:
        chat = LlmChat(
            api_key=llm_key,
            session_id=session_id,
            system_message=system_msg
        ).with_model("gemini", "gemini-2.5-flash")
        
        response = await chat.send_message_async(full_prompt)
        response_text = response.content
        
        # Save AI response to session
        await add_message_to_session(session_id, "assistant", response_text, request.module)
        
        return {
            "response": response_text,
            "module": request.module,
            "query": request.query,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"AI Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

# ==================== CONVERSATION MANAGEMENT ====================

@router.get("/sessions")
async def get_user_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """Get user's conversation sessions"""
    skip = (page - 1) * page_size
    total = await db.ai_conversations.count_documents({"user_id": user["id"]})
    
    cursor = db.ai_conversations.find(
        {"user_id": user["id"]},
        {"_id": 0, "messages": {"$slice": -1}}  # Only get last message
    ).sort("updated_at", -1).skip(skip).limit(page_size)
    
    sessions = await cursor.to_list(page_size)
    
    return {
        "items": sessions,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/sessions/{session_id}")
async def get_session_messages(session_id: str, user: dict = Depends(get_current_user)):
    """Get all messages in a session"""
    session = await db.ai_conversations.find_one(
        {"session_id": session_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """Delete a conversation session"""
    result = await db.ai_conversations.delete_one({"session_id": session_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}

@router.post("/sessions/new")
async def create_new_session(module: str = "general", user: dict = Depends(get_current_user)):
    """Create a new conversation session"""
    session = await get_or_create_session(user["id"], None, module)
    return {"session_id": session["session_id"], "module": module}

# ==================== QUICK ANALYSIS ENDPOINTS ====================

@router.get("/quick/blending-suggestion")
async def get_blending_suggestion(user: dict = Depends(get_current_user)):
    """Get quick blending suggestion without full AI query"""
    vessels = await db.vessels.find({}, {"_id": 0, "gcv_arb": 1, "ash_arb": 1, "suppliers": 1}).sort("time_arrival", -1).limit(5).to_list(5)
    barges = await db.barges.find({}, {"_id": 0, "gcv_arb": 1, "ash_arb": 1, "suppliers": 1}).sort("ta", -1).limit(5).to_list(5)
    
    all_stock = vessels + barges
    if not all_stock:
        return {"suggestion": "Tidak ada data stock untuk dianalisis", "data": []}
    
    avg_gcv = sum(s.get("gcv_arb", 0) for s in all_stock if s.get("gcv_arb")) / len([s for s in all_stock if s.get("gcv_arb")]) if all_stock else 0
    avg_ash = sum(s.get("ash_arb", 0) for s in all_stock if s.get("ash_arb")) / len([s for s in all_stock if s.get("ash_arb")]) if all_stock else 0
    
    return {
        "suggestion": f"Rata-rata GCV: {avg_gcv:.0f} kcal/kg, Rata-rata Ash: {avg_ash:.2f}%",
        "avg_gcv": avg_gcv,
        "avg_ash": avg_ash,
        "stock_count": len(all_stock)
    }

@router.get("/quick/boiler-alert")
async def get_boiler_alerts(user: dict = Depends(get_current_user)):
    """Get quick boiler risk alerts"""
    high_ash = await db.vessels.find({"ash_arb": {"$gt": 8}}, {"_id": 0}).limit(5).to_list(5)
    high_sulphur = await db.vessels.find({"ts_arb": {"$gt": 1.5}}, {"_id": 0}).limit(5).to_list(5)
    
    alerts = []
    if high_ash:
        alerts.append({"type": "warning", "message": f"{len(high_ash)} shipment dengan ash tinggi (>8%)"})
    if high_sulphur:
        alerts.append({"type": "warning", "message": f"{len(high_sulphur)} shipment dengan sulphur tinggi (>1.5%)"})
    
    if not alerts:
        alerts.append({"type": "success", "message": "Tidak ada risiko boiler terdeteksi"})
    
    return {"alerts": alerts}
