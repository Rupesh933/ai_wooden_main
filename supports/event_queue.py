import queue

subscribers = {}  # {25: [queue_1, queue_2], 24: {queue_3}, }

def subscribe(conversation_id):
    q = queue.Queue()  # create an empty queue for this browser tab

    if conversation_id not in subscribers:
        subscribers[conversation_id] = []  # {5: []}

    subscribers[conversation_id].append(q)   # {5: [queue_4]}

    return q

def unSubscribe(conversation_id, q):
    '''
    I'm either closing the tab or coming out of the tab, we just want to remove the queue from the subscribe list.
    '''
    if conversation_id in subscribers:   # {5: [queue_4]}
        subscribers[conversation_id].remove(q)  # {5: []}
        if not subscribers[conversation_id]:
            del subscribers[conversation_id]  # {}

def publish(conversation_id, event):
    """
    who is going to publish the events?
    AI agent is going to publish the event to all the queue {5: [queue_1, queue_2]}, if two staff are watching the same conversation, they will have their own queue q1, q2
    if there is someone else watching maybe q3 there for the same conversation, then it's also going to publish to q3 as well.
    """
    if conversation_id in subscribers:
        for q in subscribers[conversation_id]:
            q.put(event)

# sentinel value - it tells SSE stream to stop
DONE = {"type": "done"}