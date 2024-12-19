from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from .forms import RegistrationForm, LoginForm, TeamForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objects as go
import numpy as np
import seaborn as sns

from .models import Sprite, UserProfile
import io
import os
import urllib, base64
from .models import PokemonTeam
import csv 
import requests

pokemon_data_path = os.path.join(settings.BASE_DIR, 'pokelytics', 'static', 'All_Pokemon.csv')
pokemon_data = pd.read_csv(pokemon_data_path)

@login_required
def security_privacy(request):
    """
    View to handle security and privacy settings.
    """
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validate current password
        if not check_password(current_password, request.user.password):
            messages.error(request, "Senha atual incorreta.")
        elif new_password != confirm_password:
            messages.error(request, "As novas senhas não coincidem.")
        elif not new_password:
            messages.error(request, "A nova senha não pode estar vazia.")
        else:
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep the user logged in
            messages.success(request, "Senha atualizada com sucesso!")
            return redirect('security_privacy')

        # Update privacy settings
        user_profile.email_notifications = bool(request.POST.get('email_notifications'))
        user_profile.two_factor_auth = bool(request.POST.get('two_factor_auth'))
        user_profile.data_sharing = bool(request.POST.get('data_sharing'))
        user_profile.save()

    return render(request, 'security_privacy.html', {
        'user_profile': user_profile
    })

def get_first_team_or_redirect(user):
    """
    Get the first team belonging to the user. 
    Redirect to 'create_team' if no teams exist.
    """
    team = PokemonTeam.objects.filter(user=user).first()
    if team:
        return team.id
    else:
        return None
    
@login_required
def profile(request):
    """
    Profile view to display user details and handle profile updates.
    Redirects to create team if no team exists for the user.
    """
    # Ensure the UserProfile exists for the current user
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Check for the user's first team
    team = PokemonTeam.objects.filter(user=request.user).first()
    if not team:
        # Redirect to create team page if no team exists
        return HttpResponseRedirect(reverse('create_team'))

    if request.method == 'POST':
        # Handle form submission to update user details
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        # Update password if provided
        if password:
            user.set_password(password)
            update_session_auth_hash(request, user)  # Keep user logged in after password change

        user.save()
        messages.success(request, "Perfil atualizado com sucesso!")
        return redirect('profile')

    return render(request, 'profile.html', {
        'user': request.user,
        'user_profile': user_profile,
        'team_id': team.id,  # Pass team_id to the template
    })

@login_required
def settings(request):
    if request.method == 'POST':
        # Handle account-specific settings or password change
        password = request.POST.get('password')
        if password:
            request.user.set_password(password)
            request.user.save()
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('login')

    return render(request, 'settings.html')


@login_required
def dashboard(request):
    user_teams = PokemonTeam.objects.filter(user=request.user)
    team_plots = []

    for team in user_teams:
        # Generate charts for the team
        charts = generate_team_charts(team, pokemon_data)
        team_plots.append({
            'team_name': team.team_name,
            'heatmap': charts['heatmap'],
            'radar': charts['radar'],
        })

    return render(request, 'dashboard.html', {'teams': user_teams, 'team_plots': team_plots})


def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

from django.contrib import messages

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard
            else:
                # Add an error message for invalid credentials
                messages.error(request, 'Credenciais inválidas. Verifique o usuário ou a senha.')
        else:
            messages.error(request, 'Preencha todos os campos corretamente.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('index')


@login_required
def create_team(request):
    # Read Pokémon names from All_Pokemon.csv
    pokemon_list = pokemon_data['Name'].tolist()

    if request.method == 'POST':
        team_name = request.POST['team_name']
        pokemon = [
            request.POST.get(f'pokemon_{i}', '') for i in range(1, 7)
        ]

        # Save the team to the database
        PokemonTeam.objects.create(
            user=request.user,
            team_name=team_name,
            pokemon_1=pokemon[0],
            pokemon_2=pokemon[1],
            pokemon_3=pokemon[2],
            pokemon_4=pokemon[3],
            pokemon_5=pokemon[4],
            pokemon_6=pokemon[5],
        )
        return redirect('dashboard')

    return render(request, 'create_team.html', {'pokemon_list': pokemon_list})





def team_detail(request, team_id):
    team = get_object_or_404(PokemonTeam, id=team_id, user=request.user)
    teams = PokemonTeam.objects.filter(user=request.user)

    # Fetch Pokémon for the team
    team_pokemon = []
    for pokemon_name in [
        team.pokemon_1, team.pokemon_2, team.pokemon_3,
        team.pokemon_4, team.pokemon_5, team.pokemon_6
    ]:
        if pokemon_name:
            # Format the name to handle spaces and special characters
            formatted_name = pokemon_name.lower().replace(' ', '-')
            sprite_url = f"https://img.pokemondb.net/sprites/home/normal/{formatted_name}.png"
            team_pokemon.append({
                'name': pokemon_name,
                'sprite': sprite_url,
            })

    # Fetch stats for a specific Pokémon if clicked
    selected_pokemon_name = request.GET.get('pokemon')
    selected_pokemon = None
    if selected_pokemon_name:
        pokemon_row = pokemon_data[pokemon_data['Name'].str.lower() == selected_pokemon_name.lower()]
        if not pokemon_row.empty:
            pokemon = pokemon_row.iloc[0]
            selected_pokemon = {
                'name': pokemon['Name'],
                'hp': pokemon['HP'],
                'attack': pokemon['Att'],
                'defense': pokemon['Def'],
                'SpA': pokemon['Spa'],
                'SpD': pokemon['Spd'],
                'speed': pokemon['Spe'],
                'sprite': f"https://img.pokemondb.net/sprites/home/normal/{pokemon['Name'].lower().replace(' ', '-')}.png"
            }

    return render(request, 'team_detail.html', {
        'team': team,
        'teams': teams,
        'team_pokemon': team_pokemon,
        'selected_pokemon': selected_pokemon,
    })


@login_required
def delete_team(request, team_id):
    team = get_object_or_404(PokemonTeam, id=team_id, user=request.user)
    team.delete()
    return redirect('dashboard')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validate that passwords match
        if password != password2:
            messages.error(request, "As senhas não coincidem.")
            return render(request, 'register.html')

        # Validate if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nome de usuário já existe.")
            return render(request, 'register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, "E-mail já está em uso.")
            return render(request, 'register.html')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Conta criada com sucesso. Faça o login.")
        return redirect('login')

    return render(request, 'register.html')




# Pokemon grid clicable


RADAR_CATEGORIES = ['HP', 'Att', 'Def', 'Spa', 'Spd', 'Spe']
TYPES = ['Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison', 'Ground', 
         'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy']

def generate_team_charts(team, pokemon_data):
    weakness_matrix = []
    team_pokemon = [team.pokemon_1, team.pokemon_2, team.pokemon_3, team.pokemon_4, team.pokemon_5, team.pokemon_6]
    
    radar_data = {}  # Dictionary to hold stats for each Pokémon
    
    # Process Pokémon stats and weaknesses
    for name in team_pokemon:
        if name:
            pokemon_row = pokemon_data[pokemon_data['Name'].str.lower() == name.lower()]
            if not pokemon_row.empty:
                # Stats for Radar
                stats_values = [pokemon_row.iloc[0][col] for col in RADAR_CATEGORIES]
                radar_data[name] = stats_values
                
                # Weakness Matrix for Heatmap
                weaknesses = [pokemon_row.iloc[0][f"Against {ptype}"] for ptype in TYPES]
                weakness_matrix.append(weaknesses)

    # Custom Gradient Colors for Heatmap
    custom_colorscale = [
        (0.0, '#00ECFF'),  # 0x (Cool Blue)
        (0.0625, '#00FF64'),  # 0.25x (Bright Green)
        (0.125, '#009900'),  # 0.5x (Dark Green)
        (0.25, '#D1D1D1'),  # 1x (Light Gray)
        (0.5, '#FFC300'),  # 2x (Yellow)
        (1.0, '#FF1313')   # 4x (Bright Red)
    ]
    custom_cmap = LinearSegmentedColormap.from_list("custom_heatmap", custom_colorscale, N=256)

    # Generate the Heatmap
    buffer_heatmap = io.BytesIO()
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        weakness_matrix,
        annot=True,
        fmt=".1f",
        xticklabels=TYPES,
        yticklabels=[name if name else "N/A" for name in team_pokemon],
        cmap=custom_cmap,
        linewidths=0.5,
        vmin=0,
        vmax=4,
        cbar_kws={'label': 'Fraqueza Normalizada (0-4)'}
    )
    plt.title("Mapa de Calor - Fraqueza", fontsize=14, color="#BA3333", pad=10)
    plt.tight_layout()
    plt.savefig(buffer_heatmap, format='png', bbox_inches='tight')
    plt.close()
    heatmap_base64 = base64.b64encode(buffer_heatmap.getvalue()).decode('utf-8')

    # Generate the Radar Chart
    buffer_radar = io.BytesIO()
    plt.figure(figsize=(7, 7))

    # Set up angles for the radar chart
    angles = [n / float(len(RADAR_CATEGORIES)) * 2 * np.pi for n in range(len(RADAR_CATEGORIES))]
    angles += angles[:1]  # Close the circle

    # Pastel colors for each Pokémon
    pastel_colors = ['#FFB6C1', '#ADD8E6', '#FFDAB9', '#98FB98', '#E6E6FA', '#F0E68C']

    # Plot each Pokémon
    for i, (name, stats) in enumerate(radar_data.items()):
        stats += stats[:1]  # Close the circle
        plt.polar(angles, stats, color=pastel_colors[i % len(pastel_colors)], linewidth=2, label=name)
        plt.fill(angles, stats, color=pastel_colors[i % len(pastel_colors)], alpha=0.2)

    # Add customizations
    plt.xticks(angles[:-1], RADAR_CATEGORIES, color='#333', size=10, fontweight='bold')
    plt.title("Radar de Estatísticas", size=14, color='#BA3333', pad=10)
    plt.tight_layout()
    plt.legend(loc='upper right', fontsize=8, bbox_to_anchor=(1.1, 1.1))
    plt.savefig(buffer_radar, format='png', bbox_inches='tight')
    plt.close()
    radar_base64 = base64.b64encode(buffer_radar.getvalue()).decode('utf-8')

    return {'heatmap': heatmap_base64, 'radar': radar_base64}

def generate_team_barplots(team, pokemon_data):
    """
    Generates a bar plot for each Pokémon's stats in the team.
    Returns a dictionary with Pokémon names and their bar plot images encoded in base64.
    """
    team_pokemon = [team.pokemon_1, team.pokemon_2, team.pokemon_3, team.pokemon_4, team.pokemon_5, team.pokemon_6]
    bar_plots = {}
    
    for name in team_pokemon:
        if name:
            pokemon_row = pokemon_data[pokemon_data['Name'].str.lower() == name.lower()]
            if not pokemon_row.empty:
                # Fetch Pokémon stats
                stats = [pokemon_row.iloc[0][col] for col in RADAR_CATEGORIES]

                # Generate Bar Plot
                buffer_bar = io.BytesIO()
                plt.figure(figsize=(6, 4))
                plt.bar(RADAR_CATEGORIES, stats, color=['#FFB6C1', '#ADD8E6', '#FFDAB9', '#98FB98', '#E6E6FA', '#F0E68C'])
                plt.title(f"Estatísticas de {name}", fontsize=12, color="#333", pad=10)
                plt.ylabel("Valor")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(buffer_bar, format='png', bbox_inches='tight')
                plt.close()
                bar_plots[name] = base64.b64encode(buffer_bar.getvalue()).decode('utf-8')
    
    return bar_plots

@login_required
def team_analysis(request, team_id):
    team = PokemonTeam.objects.get(pk=team_id)
    team_pokemon = [team.pokemon_1, team.pokemon_2, team.pokemon_3, team.pokemon_4, team.pokemon_5, team.pokemon_6]

    # Prepare team Pokémon list with sprite URLs
    team_pokemon_data = []
    for name in team_pokemon:
        if name:
            formatted_name = name.lower().replace(' ', '-')
            sprite_url = f"https://img.pokemondb.net/sprites/home/normal/{formatted_name}.png"
            team_pokemon_data.append({
                'name': name,
                'sprite': sprite_url
            })

    # Filter Pokémon data for team members
    filtered_data = pokemon_data[pokemon_data['Name'].isin([p for p in team_pokemon if p])]

    # Radar Chart
    radar_fig = go.Figure()
    for _, row in filtered_data.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=[row['HP'], row['Att'], row['Def'], row['Spa'], row['Spd'], row['Spe']],
            theta=['HP', 'Attack', 'Defense', 'Sp. Attack', 'Sp. Defense', 'Speed'],
            fill='toself',
            name=row['Name']
        ))
    radar_fig.update_layout(title="Comparativo de Estatísticas", polar=dict(radialaxis=dict(visible=True)))
    radar_chart = radar_fig.to_html(full_html=False)

    # Team Heatmap
    heatmap_data = filtered_data[[col for col in pokemon_data.columns if col.startswith("Against")]].values
    heatmap_types = [col.replace("Against ", "") for col in pokemon_data.columns if col.startswith("Against")]
    team_heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=heatmap_types,
        y=filtered_data['Name'],
        colorscale=[
            [0.0, '#00ECFF'], [0.0625, '#00FF64'], [0.125, '#009900'],
            [0.25, '#D1D1D1'], [0.5, '#FFC300'], [1.0, '#FF1313']
        ],
        colorbar=dict(title="Fraqueza")
    ))
    team_heatmap_fig.update_layout(title="Mapa de Calor - Fraqueza do Time")
    team_heatmap = team_heatmap_fig.to_html(full_html=False)

    # Bar Plots for Each Pokémon
    bar_plots = {}
    for _, row in filtered_data.iterrows():
        buffer = io.BytesIO()
        plt.figure(figsize=(6, 4))
        plt.bar(['HP', 'Att', 'Def', 'Spa', 'Spd', 'Spe'], 
                [row['HP'], row['Att'], row['Def'], row['Spa'], row['Spd'], row['Spe']],
                color=['#FFB6C1', '#ADD8E6', '#FFDAB9', '#98FB98', '#E6E6FA', '#F0E68C'])
        plt.title(f"{row['Name']} - Estatísticas")
        plt.ylabel("Valores")
        plt.tight_layout()
        plt.savefig(buffer, format="png")
        plt.close()
        bar_plots[row['Name']] = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render(request, 'team_analysis.html', {
        'team': team,
        'team_pokemon': team_pokemon_data,
        'radar_chart': radar_chart,
        'team_heatmap': team_heatmap,
        'bar_plots': bar_plots
    })


def pokemon_detail(request, pokemon_name):
    # Match the Pokémon name exactly (case insensitive)
    pokemon = pokemon_data[pokemon_data['Name'].str.lower() == pokemon_name.lower()].iloc[0]

    # Prepare the stats to send to the template
    stats = {
        'name': pokemon['Name'],
        'hp': pokemon['HP'] or 0,
        'attack': pokemon['Att'] or 0,
        'defense': pokemon['Def'] or 0,
        'SpA': pokemon['Spa'] or 0,
        'SpD': pokemon['Spd'] or 0,
        'Speed': pokemon['Spe'] or 0,
        'type1': pokemon['Type 1'],
        'type2': pokemon['Type 2'] if pd.notnull(pokemon['Type 2']) else None,
        'sprite': f"https://img.pokemondb.net/sprites/home/normal/{pokemon['Name'].lower().replace(' ', '-')}.png"
    }


    return render(request, 'pokemon_detail.html', {'stats': stats})


