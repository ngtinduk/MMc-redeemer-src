from queue import Queue

def create_queue(items: list, multiplier: int = 1) -> Queue:
    q = Queue()
    
    for item in items:
        for _ in range(multiplier):
            q.put_nowait(item)
        
    return q

def queue_safe_get(q: Queue) -> None | str:
    if q.empty(): return None
    
    return q.get_nowait()