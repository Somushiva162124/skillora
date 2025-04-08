from .models import UserProfile

def gamification_context(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {
                'xp': profile.xp,
                'level': profile.level
            }
        except UserProfile.DoesNotExist:
            pass
    return {
        'xp': None,
        'level': None
    }
