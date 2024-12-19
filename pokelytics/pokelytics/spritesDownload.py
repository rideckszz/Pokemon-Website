import os
import requests
import pandas as pd
from tqdm import tqdm  # For progress bar

# Path to the CSV containing Pokémon names
CSV_PATH = 'pokelytics\pokelytics\static\All_Pokemon.csv'  # Adjust this path based on your project structure

# Base URL for Pokémon sprites
SPRITE_BASE_URL = "https://img.pokemondb.net/sprites/home/normal/"

# Directory to save sprites
OUTPUT_FOLDER = "static/Pokeball"


def download_pokemon_sprites():
    # Ensure the output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Load Pokémon names from the CSV file
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return
    
    pokemon_data = pd.read_csv(CSV_PATH)
    pokemon_names = pokemon_data['Name'].tolist()

    print(f"Found {len(pokemon_names)} Pokémon to download.")

    # Download sprites for each Pokémon
    for name in tqdm(pokemon_names, desc="Downloading Sprites"):
        formatted_name = name.lower().replace(" ", "-").replace(".", "")
        sprite_url = f"{SPRITE_BASE_URL}{formatted_name}.png"
        save_path = os.path.join(OUTPUT_FOLDER, f"{formatted_name}.png")

        # Skip if the sprite already exists
        if os.path.exists(save_path):
            continue

        try:
            response = requests.get(sprite_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)
            else:
                print(f"Failed to download {name}: {sprite_url}")
        except Exception as e:
            print(f"Error downloading {name}: {e}")

    print("Sprite download completed!")


if __name__ == "__main__":
    download_pokemon_sprites()
