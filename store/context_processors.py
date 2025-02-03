# your_app/context_processors.py
from .models import Message

def unread_message_count(request):
    unread_count = 0
    if request.user.is_authenticated:
        # Use 'recipient' instead of 'user'!
        unread_count = Message.objects.filter(
            recipient=request.user,  # <-- Fix here
            is_read=False
        ).count()
    return {'unread_message_count': unread_count}