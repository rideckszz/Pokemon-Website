from django.db import models
from django.contrib.auth.models import User

class Sprite(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Pokémon name
    url = models.URLField()  # Sprite URL

    def __str__(self):
        return self.name
    
class PokemonTeam(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    pokemon_1 = models.CharField(max_length=50)
    pokemon_2 = models.CharField(max_length=50)
    pokemon_3 = models.CharField(max_length=50)
    pokemon_4 = models.CharField(max_length=50)
    pokemon_5 = models.CharField(max_length=50)
    pokemon_6 = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.team_name} ({self.user.first_name} {self.user.last_name})"

# UserProfile Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.CharField(max_length=255, default='Sprites/beedrill.png')

    def __str__(self):
        return self.user.username
