"""LangGraph orchestration with deterministic routing and optional local Ollama phrasing."""
import re
import time
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services import telecom_tools as tools


class State(TypedDict, total=False):
    message: str; customer_id: str; intent: str; answer: str; pending_ticket: dict; metrics: dict[str, float]

def classify(message: str) -> str:
    m = message.lower()
    if re.search(r"\bt-[a-f0-9]{8}\b", m): return "ticket_status"
    if any(x in m for x in ["اشتراك", "باقتي", "الباقة"]): return "subscription"
    if any(x in m for x in ["استهلاك", "جيجا", "دقائق", "استخدام"]): return "usage"
    if any(x in m for x in ["تذكرة", "طلب الدعم", "شكوى", "مشكلة", "عطل", "انقطاع"]): return "ticket"
    if any(x in m for x in ["العروض", "الباقات المتاحة", "الخطط"]): return "plans"
    return "unknown"

async def route(state: State): return {"intent": classify(state["message"])}

async def respond(state: State):
    started = time.perf_counter(); intent, cid, msg = state["intent"], state["customer_id"], state["message"]
    pending = None
    if intent == "subscription": data, answer = await tools.get_subscription_details(cid), ""
    elif intent == "usage": data, answer = await tools.get_usage_summary(cid), ""
    elif intent == "plans": data, answer = await tools.list_available_plans(cid), ""
    elif intent == "ticket_status":
        ticket_id = re.search(r"t-[a-f0-9]{8}", msg.lower()).group(0)
        data, answer = await tools.check_ticket_status(cid, ticket_id), ""
    elif intent == "ticket":
        # Creation is deliberately two-turn; no model or utterance can bypass confirmation.
        pending = {"subject": "طلب دعم", "description": msg}
        data, answer = {}, "هل تريد أن أنشئ تذكرة دعم بهذا الطلب؟ قل نعم للتأكيد أو لا للإلغاء."
    else: data, answer = {}, "لم أفهم الطلب بالكامل. يمكنني المساعدة في الباقات أو الاستهلاك أو تذاكر الدعم."
    if not answer:
        if "error" in data: answer = data["error"]
        elif intent == "subscription": answer = f"اشتراكك الحالي هو {data['plan']} بسعر {data['monthly_price_egp']} جنيه شهرياً ويشمل {data['data_gb']} جيجابايت."
        elif intent == "usage": answer = f"استهلاكك لشهر {data['period']} هو {data['data_gb']} جيجابايت و{data['minutes']} دقيقة."
        elif intent == "ticket_status": answer = f"حالة التذكرة {data['ticket_id']} هي: {data['status']}."
        else: answer = "الباقات المتاحة: " + "، ".join(f"{p['name']} ({p['price_egp']} جنيه، {p['data_gb']} جيجابايت)" for p in data['plans'])
    return {"answer": answer, "pending_ticket": pending, "metrics": {"tool_ms": round((time.perf_counter()-started)*1000, 1)}}

graph_builder = StateGraph(State)
graph_builder.add_node("route", route); graph_builder.add_node("respond", respond)
graph_builder.set_entry_point("route"); graph_builder.add_edge("route", "respond"); graph_builder.add_edge("respond", END)
graph = graph_builder.compile()

async def invoke(message: str, customer_id: str) -> dict:
    # Qwen/Ollama is intentionally not trusted to make authorization/tool decisions.
    return await graph.ainvoke({"message": message, "customer_id": customer_id})
