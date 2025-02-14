# your_app/context_processors.py
from .models import *

def unread_message_count(request):
    unread_count = 0
    if request.user.is_authenticated:
        # Use 'recipient' instead of 'user'!
        unread_count = Message.objects.filter(
            recipient=request.user,  # <-- Fix here
            is_read=False
        ).count()

    return {'unread_message_count': unread_count}



# yourapp/context_processors.py
def team_member(request):
    team_member = None
    if request.user.is_authenticated:
        team_member = TeamMember.objects.filter(user=request.user).first()
    print('Team Member:', team_member)  # Debugging line
    return {'team_member': team_member}
