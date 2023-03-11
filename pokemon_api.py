from fastapi import FastAPI, Depends
from enum import Enum
from pydantic import BaseModel, ValidationError, validator
from database import client
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from email_validator import validate_email, EmailNotValidError

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

DB = "pokemondb"
COLLECTION = "pokemoncollection"

def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )

def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user


class User(BaseModel):
    username: str
    password: str
    email: str

    @validator("password")
    def valid_password(cls, password: str):
        required_characters = set(["!", "@", "#", "?", "]"])
        length_compliant = len(password) >= 10
        capitalization_compliant = not password.islower() and not password.isupper()
        character_compliant = any([char in password for char in required_characters])
        if not (length_compliant and capitalization_compliant and character_compliant):
            raise ValueError("""Password needs to follow all these rules:
                - Have an uppercase character
                - Have a lowercase character
                - Be at least 10 chars long
                - Have one of the following symbols: !, @, #, ?, ]
                
                Try registering again with a valid password!
            """)

        
    @validator("email")
    def valid_email(cls, email):
        try:
            validation = validate_email(email, check_deliverability=False)
            # Normalize the email before using it further.
            email = validation.email
        except EmailNotValidError as e:
            print(str(e))
        return email



class PokemonType(str, Enum):
    grass = "grass"
    fire = "fire"
    water = "water"
    electric = "electric"
    ghost = "ghost"
    ground = "ground"
    dragon = "dragon"
    flying = "flying"
    normal = "normal"
    ice = "ice"
    fighting = "fighting"
    poison = "poison"
    bug = "bug"
    rock = "rock"
    psychic = "psychic"
    dark = "dark"
    steel = "steel"
    fairy = "fairy"

class BaseStatTotal(BaseModel):
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    health_points: int
    class Config:
        schema_extra = {
            "example": {
                "attack": 100,
                "defense": 100,
                "special_attack": 100,
                "special_defense": 100,
                "speed": 100,
                "health_points": 100,
            }
        }

class Pokemon(BaseModel):
    english_name: str
    pokedex_number: int
    primary_type: PokemonType
    secondary_type: PokemonType | None = None
    base_stat_total: BaseStatTotal
    class Config:
        schema_extra = {
            "example": {
                "english_name": "Mew",
                "pokedex_number": 151,
                "primary_type": PokemonType.psychic.value,
                "secondary_type": None,
                "base_stat_total": BaseStatTotal(
                    attack=100,
                    defense=100,
                    special_attack=100,
                    special_defense=100,
                    speed=100,
                    health_points=100),
            }
        }



@app.get("/")
def root():
    return {"message": "Welcome to the world of Pokémon! Some of our services require you to register and login"}

# @app.post("/users/")
# def create_new_user(user: User):
#     return User

@app.get("/users/me")
async def get_my_user(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/pokemon/{english_name}")
def get_pokemon_by_name(english_name: str) -> Pokemon | None:
    pokemon_collection = client[DB][COLLECTION]
    english_name = english_name.title()  #TODO: Change this to a validator in the pokemon class?
    pokemon = pokemon_collection.find_one({"english_name": english_name})
    return pokemon

# TODO: fix
@app.get("/pokemon/{pokedex_number}")
def get_pokemon_by_dex_number(pokedex_number: int) -> Pokemon | None:
    pokemon_collection = client[DB][COLLECTION]
    pokemon = pokemon_collection.find_one({"pokedex_number": pokedex_number})
    return pokemon

@app.get("/pokemon/")
def get_all_pokemon(skip: int = 0, limit: int = 10) -> list[Pokemon]:
    pokemon_collection = client[DB][COLLECTION]
    pokemon_list = list(pokemon_collection.find()[skip: skip + limit])
    return pokemon_list

@app.post("/pokemon/")
def create_pokemon(pokemon: Pokemon) -> Pokemon:
    pokemon.english_name = pokemon.english_name.title()
    pokemon = jsonable_encoder(pokemon)
    client[DB][COLLECTION].insert_one(pokemon)
    return pokemon

