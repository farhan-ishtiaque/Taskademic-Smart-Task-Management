from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid


class Team(models.Model):
    """Simple team model for task sharing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    invite_code = models.CharField(max_length=8, unique=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)
        # Auto-add creator as member
        if self.pk and not self.members.filter(id=self.created_by.id).exists():
            self.members.add(self.created_by)
    
    def generate_invite_code(self):
        """Generate unique 6-character invite code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Team.objects.filter(invite_code=code).exists():
                return code
    
    @property
    def member_count(self):
        return self.members.count()


class TeamInvite(models.Model):
    """Email-based team invitations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='email_invites')
    email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invite_token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['team', 'email']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invite to {self.team.name} for {self.email}"
    
    def save(self, *args, **kwargs):
        if not self.invite_token:
            self.invite_token = self.generate_invite_token()
        if not self.expires_at:
            # Invite expires in 7 days
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def generate_invite_token(self):
        """Generate unique invite token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @property
    def is_expired(self):
        """Check if invite has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if invite is still valid"""
        return not self.is_accepted and not self.is_expired
    
    def send_invite_email(self):
        """Send invitation email"""
        invite_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/teams/accept-invite/{self.invite_token}/"
        
        subject = f"You're invited to join {self.team.name} on Taskademic"
        message = f"""
Hello!

{self.invited_by.get_full_name() or self.invited_by.username} has invited you to join the team "{self.team.name}" on Taskademic.

Team Description: {self.team.description or 'No description provided'}

To accept this invitation, click the link below:
{invite_url}

This invitation will expire on {self.expires_at.strftime('%B %d, %Y at %I:%M %p')}.

If you don't have a Taskademic account yet, you'll be prompted to create one.

Best regards,
The Taskademic Team
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@taskademic.com'),
                recipient_list=[self.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending invite email: {e}")
            return False
    
    def accept_invite(self, user):
        """Accept the invitation and add user to team"""
        if not self.is_valid:
            return False, "Invitation has expired or already been accepted"
        
        if user.email.lower() != self.email.lower():  # Case-insensitive comparison
            return False, "Email doesn't match the invitation"
        
        # Add user to team
        self.team.members.add(user)
        
        # Mark invitation as accepted
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()
        
        return True, f"Successfully joined {self.team.name}!"
