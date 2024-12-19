from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginForm, TeamForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

import io
import os
import urllib, base64
from .models import PokemonTeam
import csv 
import requests

pokemon_data_path = os.path.join(settings.BASE_DIR, 'pokelytics', 'static', 'All_Pokemon.csv')
pokemon_data = pd.read_csv(pokemon_data_path)



@login_required
def dashboard(request):
    user_teams = PokemonTeam.objects.filter(user=request.user)
    team_plots = []

    # Generate a bar chart for each team
    for team in user_teams:
        # Example data for each Pokémon's stats
        pokemon_names = [
            team.pokemon_1, team.pokemon_2, team.pokemon_3,
            team.pokemon_4, team.pokemon_5, team.pokemon_6
        ]
        stats_labels = ['HP', 'Attack', 'Defense', 'Sp. Attack', 'Sp. Defense', 'Speed']
        combined_stats = [0] * len(stats_labels)

        # Sum stats for the team Pokémon
        for name in pokemon_names:
            if name:
                pokemon_row = pokemon_data[pokemon_data['Name'].str.lower() == name.lower()]
                if not pokemon_row.empty:
                    pokemon = pokemon_row.iloc[0]
                    stats_values = [pokemon['HP'], pokemon['Att'], pokemon['Def'], pokemon['Spa'], pokemon['Spd'], pokemon['Spe']]
                    combined_stats = [x + y for x, y in zip(combined_stats, stats_values)]

        # Create the bar chart
        plt.figure(figsize=(6, 4))
        plt.bar(stats_labels, combined_stats, color='skyblue')
        plt.title(f"Stats Totais - {team.team_name}")
        plt.tight_layout()

        # Convert the plot to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        team_plots.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))
        plt.close()

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
def dashboard(request):
    # Fetch only the teams belonging to the current user
    user_teams = PokemonTeam.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {'teams': user_teams})

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


def generate_chart(pokemon):
    stats_labels = ['HP', 'Attack', 'Defense', 'Sp. Attack', 'Sp. Defense', 'Speed']
    stats_values = [pokemon['HP'], pokemon['Att'], pokemon['Def'], pokemon['Spa'], pokemon['Spd'], pokemon['Spe']]

    plt.figure(figsize=(4, 4))
    plt.bar(stats_labels, stats_values, color=['red', 'blue', 'green', 'purple', 'orange', 'cyan'])
    plt.title(f"{pokemon['Name']} Stats")
    plt.ylabel('Value')
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close('all')
    return chart_base64




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

@login_required
def team_analysis(request, team_id):
    # Fetch team and Pokémon details
    team = get_object_or_404(PokemonTeam, id=team_id, user=request.user)
    teams = PokemonTeam.objects.filter(user=request.user)  # Ensure all user teams are loaded

    selected_pokemon_names = [
        team.pokemon_1, team.pokemon_2, team.pokemon_3,
        team.pokemon_4, team.pokemon_5, team.pokemon_6
    ]

    # Filter Pokémon data
    filtered_data = pokemon_data[pokemon_data['Name'].isin(selected_pokemon_names)]

    # Generate Radar Chart
    radar_fig = go.Figure()
    for _, row in filtered_data.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=row[RADAR_CATEGORIES].values,
            theta=RADAR_CATEGORIES,
            fill='toself',
            name=row['Name']
        ))
    radar_fig.update_layout(
        title="Comparativo de Estatísticas (Radar)",
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True
    )
    radar_html = radar_fig.to_html(full_html=False)

    # Generate Stacked Bar Chart
    bar_fig = go.Figure()
    for _, row in filtered_data.iterrows():
        bar_fig.add_trace(go.Bar(
            x=RADAR_CATEGORIES,
            y=row[RADAR_CATEGORIES].values,
            name=row['Name']
        ))
    bar_fig.update_layout(
        title="Estatísticas Empilhadas por Pokémon",
        barmode='stack',
        xaxis_title="Atributos",
        yaxis_title="Valores"
    )
    bar_html = bar_fig.to_html(full_html=False)

    # Generate Matchup Heatmaps for Each Pokémon
    against_columns = [col for col in pokemon_data.columns if col.startswith('Against')]
    matchup_graphs = {}
    for _, row in filtered_data.iterrows():
        matchups = row[against_columns].values
        types = [col.replace('Against ', '') for col in against_columns]

        heatmap_fig = go.Figure(data=[
            go.Bar(
                x=types,
                y=matchups,
                marker=dict(color=matchups, colorscale='Viridis'),
                text=[f"{v:.2f}" for v in matchups],
                textposition='auto'
            )
        ])
        heatmap_fig.update_layout(
            title=f"Fraquezas de {row['Name']} (Mapa de Calor)",
            xaxis_title="Tipos",
            yaxis_title="Multiplicador de Dano"
        )
        matchup_graphs[row['Name']] = heatmap_fig.to_html(full_html=False)

    # Pokémon cards for the bottom section
    team_pokemon = []
    for name in selected_pokemon_names:
        if name:
            sprite_url = f"https://img.pokemondb.net/sprites/black-white/normal/{name.lower()}.png"
            team_pokemon.append({'name': name, 'sprite': sprite_url})

    return render(request, 'team_analysis.html', {
        'team': team,
        'teams': teams,  # Sidebar teams
        'radar_chart': radar_html,
        'bar_chart': bar_html,
        'matchup_graphs': matchup_graphs,
        'team_pokemon': team_pokemon  # Pokémon details for the bottom grid
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
