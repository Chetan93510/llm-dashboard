"""
Middleware to automatically set user_id for logged-in users
"""

class UserIDMiddleware:
    """Middleware to inject user email as user_id in request context"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add user_id to request if user is authenticated
        if request.user.is_authenticated:
            request.user_id = request.user.email
        else:
            request.user_id = None
        
        response = self.get_response(request)
        return response
