from django.db import models

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
            return self.title
    
class TeamTask(models.Model):
    title = models.CharField(max_length = 200)
    completed = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
            return self.title

class UserAccount(models.Model):
      ROLE_CHOICES = [
            ('leader', 'Leader'),
            ('member', 'Member'),
      ]

      user_id = models.AutoField(primary_key=True)
      username = models.CharField(max_length=100, unique=True)
      email = models.EmailField(unique=True)
      password = models.CharField(max_length=255)
      role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")

      def __str__(self):
            return f"{self.username} ({self.role})"
      
class Team(models.Model):
      team_id = models.AutoField(primary_key=True)
      team_name = models.CharField(max_length=100, unique=True)
      team_desc = models.CharField(max_length=255)

      def __str__(self):
            return self.team_name

class TeamMember(models.Model):
      ROLE_CHOICES = [
            ('leader', 'Leader'),
            ('member', 'Member'),
      ]

      team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='members')
      user = models.ForeignKey('UserAccount', on_delete=models.CASCADE, related_name='teams')
      role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')

      class Meta:
            unique_together = ('team', 'user')
      def __str__(self):
            return f"{self.user.username} - {self.role} of {self.Team.team_name}"
      