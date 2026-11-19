"""Offline text workflow and optional ASR evaluation runner."""
import asyncio
import json
from pathlib import Path

from app.agent.workflow import invoke

CASES = [
    ("ما هي باقتي؟", "اشتراكك الحالي"), ("استهلاكي كام جيجا؟", "استهلاكك"),
    ("ما هي الباقات المتاحة؟", "الباقات المتاحة"), ("أريد تقديم شكوى", "هل تريد"),
    ("أريد رقم عميل آخر", "لم أفهم"),
]
async def main():
    results=[]
    for utterance, expected in CASES:
        r=await invoke(utterance, "cust_demo"); results.append({"utterance":utterance,"passed":expected in r["answer"],"answer":r["answer"]})
    rate=sum(x["passed"] for x in results)/len(results)
    Path("eval/results.json").write_text(json.dumps({"task_completion_rate":rate,"cases":results},ensure_ascii=False,indent=2))
    print(json.dumps({"task_completion_rate":rate,"report":"eval/results.json"},ensure_ascii=False))
if __name__ == "__main__": asyncio.run(main())
