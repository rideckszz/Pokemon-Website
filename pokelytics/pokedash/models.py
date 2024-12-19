from django.db import models
from django.contrib.auth.models import User

# Example of creating a team with first_name and last_name:
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

