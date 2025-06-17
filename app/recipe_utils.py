
from datetime import datetime  
import requests
import os
import google.generativeai as genai
import re
import json
import pandas as pd
from rapidfuzz import process
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from googletrans import Translator


load_dotenv()

SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Load disease dataset
DATASET_PATH = "C:/Users/MANISHA/Downloads/RecipeChatbot/RecipeChatbot/modified_disease_nutrient_dataset_updated.csv"
# Path to synonym CSV
SYNONYM_PATH = "C:/Users/MANISHA/Downloads/RecipeChatbot/RecipeChatbot/synonyms.csv"  

synonym_df = pd.read_csv(SYNONYM_PATH)
disease_data = pd.read_csv(DATASET_PATH)
diseases = disease_data["Disease Name"].dropna().unique().tolist()

model1 = SentenceTransformer('all-MiniLM-L6-v2')
disease_embeddings = model1.encode(diseases, convert_to_tensor=True)

# Load API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0,
    )
)

def fuzzy_fix(user_input, choices, cutoff=60):
    lower_choices = {c.lower(): c for c in choices}
    match = process.extractOne(user_input.lower(), lower_choices.keys(), score_cutoff=cutoff)
    return lower_choices[match[0]] if match else user_input

def match_disease(user_input):
    if not user_input:
        return [], []
    disease_inputs = [d.strip() for d in user_input.split(',') if d.strip()]
    matched = []
    scores = []
    for entry in disease_inputs:
        cleaned = fuzzy_fix(entry, diseases)
        embedding = model1.encode(cleaned, convert_to_tensor=True)
        sim_scores = util.cos_sim(embedding, disease_embeddings)[0]
        idx = sim_scores.argmax().item()
        matched.append(diseases[idx])
        scores.append(sim_scores[idx].item())
    return matched, scores

def parse_safe_limits(limit_str):
    parsed = {}
    for item in str(limit_str).split(","):
        parts = item.strip().split(":")
        if len(parts) == 2:
            nutrient, value = parts
            amt, unit = extract_amount_and_unit(value)
            parsed[nutrient.strip()] = convert_to_grams(amt, unit)
    return parsed

def extract_amount_and_unit(nutrient_str):
    amount_match = re.search(r"[\d.]+", nutrient_str)
    unit_match = re.search(r"[a-zA-Z\u00b5]+", nutrient_str)
    if amount_match:
        amount = float(amount_match.group(0))
    else:
        return 0.0, ""
    unit = unit_match.group(0) if unit_match else "g"
    return amount, unit

def convert_to_grams(amount, unit):
    unit = unit.lower()
    conversion_factors = {"g": 1, "mg": 0.001, "µg": 0.000001, "mcg": 0.000001}
    return amount * conversion_factors.get(unit, 1)

def merge_diseases(disease_list):
    bad_ingredients = set()
    nutrient_limits = {}
    for disease in disease_list:
        row = disease_data[disease_data["Disease Name"] == disease]
        if not row.empty:
            row = row.iloc[0]
            bad_ings = [b.strip().lower() for b in str(row["Bad Ingredients"]).split(",") if b.strip()]
            limits = parse_safe_limits(row["Bad Nutrients Safe Limits (mg/g)"])
            bad_ingredients.update(bad_ings)
            for nutrient, limit in limits.items():
                nutrient_limits[nutrient] = min(nutrient_limits.get(nutrient, float("inf")), limit)
    return list(bad_ingredients), nutrient_limits

def get_recipes_by_ingredients(ingredients):
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ingredients,
        "number": 5,
        "ignorePantry": True,
        "ranking": 1,
        "apiKey": SPOONACULAR_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else []

def get_random_recipes():
    url = "https://api.spoonacular.com/recipes/random"
    response = requests.get(url, params={"number": 5, "apiKey": SPOONACULAR_API_KEY})
    return response.json().get("recipes", []) if response.status_code == 200 else []

def fetch_recipe_nutrients(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"
    response = requests.get(url, params={"apiKey": SPOONACULAR_API_KEY})
    if response.status_code != 200: return {}
    data = response.json()
    nutrients = {}
    for n in data.get("bad", []):
        amount, unit = extract_amount_and_unit(n["amount"])
        nutrients[n["title"]] = convert_to_grams(amount, unit)
    return nutrients

def filter_user_ingredients(user_ingredients, bad_ingredients):
    return [ing.lower() for ing in user_ingredients if not any(bad in ing.lower() or ing.lower() in bad for bad in bad_ingredients)]

def has_bad_ingredient(recipe_ingredients, bad_ingredients):
    names = [ing["name"].lower() for ing in recipe_ingredients]
    return any(any(bad in name or name in bad for bad in bad_ingredients) for name in names)

def contains_all_safe_ingredients(recipe_ingredients, safe_ingredients):
    names = [ing["name"].lower() for ing in recipe_ingredients]
    return all(any(safe in name or name in safe for name in names) for safe in safe_ingredients)

def count_extra_ingredients(recipe_ingredients, safe_ingredients):
    recipe_names = set(ing["name"].lower() for ing in recipe_ingredients)
    return len(recipe_names - set(safe_ingredients))

def filter_recipes(bad_ingredients, safe_limits, recipes, safe_ingredients=None, enforce_safe_ingredients=False):
    safe_recipes = []
    for r in recipes:
        recipe_id = r["id"]
        title = r["title"]
        image=r["image"]
        print(f"\n🔍 Checking Recipe: {title} (ID: {recipe_id})")
        ingredients = r.get("usedIngredients", []) + r.get("missedIngredients", []) + r.get("extendedIngredients", [])

        if has_bad_ingredient(ingredients, bad_ingredients):
            print("❌ Rejected: Contains bad ingredient")
            continue
        if enforce_safe_ingredients and not contains_all_safe_ingredients(ingredients, safe_ingredients):
            print("❌ Rejected: Does not contain all safe ingredients")
            continue
        nutrients = fetch_recipe_nutrients(recipe_id)
        if any(nutrients.get(n, 0) > limit for n, limit in safe_limits.items()):
            print("❌ Rejected: Nutrient limit exceeded")
            continue
        if safe_ingredients is None:
            safe_ingredients = []
        elif not isinstance(safe_ingredients, list):
            safe_ingredients = list(safe_ingredients)
        extra_count = count_extra_ingredients(ingredients, safe_ingredients)
        safe_recipes.append({
            "title": title, 
            "id": recipe_id,
            "image":image, 
            "usedIngredientCount":r.get("usedIngredientCount", []),
            "missedIngredientCount":r.get("missedIngredientCount", []),
            "extra_count": extra_count
        })
        print("✅ Accepted recipe ✅")
    return sorted(safe_recipes, key=lambda x: x["extra_count"])

def get_fallback_recipes(bad_ingredients, safe_limits, safe_ingredients):
    print("\n🔄 Fetching fallback recipes...")
    fallback_recipes = []
    for _ in range(1):
        random_recipes = get_random_recipes()
        filtered = filter_recipes(
            bad_ingredients,
            safe_limits,
            random_recipes,
            safe_ingredients,
            enforce_safe_ingredients=False
        )
        fallback_recipes.extend(filtered)
        if fallback_recipes:
            break
    return fallback_recipes

def get_safe_recipes(ingredients_input, bad_ingredients,safe_limits):
    safe_ingredients = filter_user_ingredients(ingredients_input, bad_ingredients)
    print(f"\n🥦 Filtered Safe Ingredients: {safe_ingredients}")

    safe_recipes = []
    if safe_ingredients:
        recipes = get_recipes_by_ingredients(",".join(safe_ingredients))
        print(f"\n📦 Retrieved {len(recipes)} recipes.")
        # print("Recipes are--->>>>",recipes)
        safe_recipes = filter_recipes(bad_ingredients, safe_limits, recipes, safe_ingredients, enforce_safe_ingredients=True)
    else:
        print("\n⚠️ No safe ingredients left. Skipping safe recipe suggestion.")

    fallback_recipes = get_fallback_recipes(bad_ingredients, safe_limits, safe_ingredients)
    print("\nSafe recipes-> ",safe_recipes)
    print("fallback_recipes-->>>",fallback_recipes)
    return {"safe_recipes": safe_recipes, "fallback_recipes": fallback_recipes}

# --------------- Synonym Expansion -------------------
def expand_bad_ingredients_with_synonyms(bad_ingredients, synonym_df):
    expanded = set(bad_ingredients)
    for bad in bad_ingredients:
        bad_lower = bad.lower()
        # Match if bad is contained in category OR category is contained in bad
        matching = synonym_df[
            synonym_df['Category'].str.lower().apply(lambda x: bad_lower in x or x in bad_lower)
        ]
        for _, row in matching.iterrows():
            synonyms = str(row['Ingredient Synonyms']).split(',')
            for syn in synonyms:
                if syn.strip():
                    expanded.add(syn.strip().lower())
    return list(expanded)


def extract_disease_and_ingredients(user_input):
    """
    Uses Gemini to extract disease and ingredients from user input
    Returns: (disease, ingredients_list)
    """
    prompt = f"""
    Extract health condition/disease and ingredients from this message.
    Return as a valid JSON object with 'disease' and 'ingredients' keys.
    If no disease found, set 'disease' to null.
    Ingredients should be a list of strings.
    Only return the JSON object, nothing else.

    Example response for "I have diabetes, gout, hypertension and want recipes with chicken and vegetables":
    {{
        "disease": "diabetes,gout,hypertension",
        "ingredients": ["chicken", "vegetables"]
    }}

    Message: "{user_input}"
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean the response to ensure valid JSON
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Debugging output
        print("Raw Gemini response:", response_text)
        
        extracted_data = json.loads(response_text)
        
        # Validate the response structure
        disease = extracted_data.get('disease')
        ingredients = extracted_data.get('ingredients', [])
        
        if not isinstance(ingredients, list):
            ingredients = []
        
        return disease, ingredients
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}. Response was: {response_text}")
        # Fallback to regular ingredient extraction
        include, exclude, _ = extract_include_exclude_ingredients(user_input)
        return None, include
        
    except Exception as e:
        print(f"Error extracting disease/ingredients: {e}")
        # Fallback to regular ingredient extraction
        include, exclude, _ = extract_include_exclude_ingredients(user_input)
        return None, include

def extract_include_exclude_ingredients(text):
    text = text.lower()

    exclusion_starters = r"(?:without|exclude|excluding|no|don't want|do not want|avoid|skip|leave out|i hate|i don't like)"

    include_patterns = [
        rf"(?:with|include|including|having|containing|have|i have)\s+([\w\s,]+?)(?=\s*{exclusion_starters}|[.?!]|$)",
        rf"(?:available ingredients|things i have|my ingredients are)\s+([\w\s,]+?)(?=\s*{exclusion_starters}|[.?!]|$)"
    ]

    exclude_patterns = [
        rf"{exclusion_starters}\s+([\w\s,]+?)(?:[.?!]|$)"
    ]

    def find_ingredients(patterns, source_text):
        found = []
        for pattern in patterns:
            matches = re.findall(pattern, source_text)
            found.extend(matches)
        return found

    def split_ingredients(phrase_list):
        ingredients = []
        for phrase in phrase_list:
            parts = re.split(r",|\band\b|\bor\b", phrase)
            ingredients.extend([p.strip() for p in parts if p.strip()])
        return ingredients

    sentences = re.split(r"\.\s*", text)
    include_phrases, exclude_phrases = [], []

    for sentence in sentences:
        include_phrases += find_ingredients(include_patterns, sentence)
        exclude_phrases += find_ingredients(exclude_patterns, sentence)

    included_ingredients = split_ingredients(include_phrases)
    excluded_ingredients = split_ingredients(exclude_phrases)

    bad_tokens = {"i", "don", "don't", "am", "using", "are", "also"}
    included_ingredients = list({ing for ing in included_ingredients if ing not in bad_tokens})
    excluded_ingredients = list({ing for ing in excluded_ingredients if ing not in bad_tokens})

    diet_keywords = ["vegan", "vegetarian", "gluten free", "keto", "ketogenic", "paleo", "low fodmap", "whole30", "dairy free", "soy free"]
    diet = next((d for d in diet_keywords if d in text), None)

    return included_ingredients, excluded_ingredients, diet

def search_recipes(include_ingredients=None, exclude_ingredients=None, diet=None):
    print("inside search recipes---")
    include_ingredients = include_ingredients or []
    exclude_ingredients = exclude_ingredients or []
    print("include ingredients->",include_ingredients)
    if not include_ingredients:
        return {
            "status": "error",
            "message": "Please provide at least some ingredients to search for recipes."
        }

    try:
        if not exclude_ingredients and not diet:
            include_str = ",".join(include_ingredients)
            url = (
                f"https://api.spoonacular.com/recipes/findByIngredients"
                f"?ingredients={include_str}"
                f"&number=5"
                f"&ranking=1"
                f"&ignorePantry=true"
                f"&apiKey={SPOONACULAR_API_KEY}"
            )

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "status": "no_results",
                    "message": "Couldn't find any recipes with these ingredients."
                }
            # print("find by ingredients data---->>>",data)
            result_list = []
            for recipe in data:
                result_list.append({
                    "id": recipe["id"],
                    "title": recipe["title"],
                    "image": recipe["image"],
                    "usedIngredientCount": recipe.get("usedIngredientCount",0),
                    "missedIngredientCount": recipe.get("missedIngredientCount",0)
                })

            return {
                "status": "success",
                "recipes": result_list
            }

        include_str = ",".join(include_ingredients)
        exclude_str = ",".join(exclude_ingredients)
        print("include str->",include_str)
        print("exclude str->",exclude_str)
        url = (
            f"https://api.spoonacular.com/recipes/complexSearch"
            f"?includeIngredients={include_str}"
            f"&excludeIngredients={exclude_str}"
            f"&number=5"
            f"&addRecipeInformation=true"
            f"&apiKey={SPOONACULAR_API_KEY}"
        )

        if diet:
            url += f"&diet={diet.lower()}"

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("data in search recipes complex search->>",data)
        recipes = data.get("results", [])

        if not recipes:
            return {
                "status": "no_results",
                "message": "Couldn't find any recipes with these constraints."
            }

        result_list = []
        for recipe in recipes:
            result_list.append({
                "id": recipe["id"],
                "title": recipe["title"],
                "image": recipe["image"],
                "readyInMinutes": recipe["readyInMinutes"],
                "servings": recipe["servings"],
                "sourceUrl": recipe["sourceUrl"]
            })

        return {
            "status": "success",
            "recipes": result_list
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipes: {e}")
        return {
            "status": "error",
            "message": "Error fetching recipes. Please try again later."
        }

def chatbot_response(user_input):
    user_input = user_input.strip()
    
    # Check if this is a recipe name query
    recipe_query_patterns = [
        r'how to make (.*)',
        r'recipe for (.*)',
        r'how do i make (.*)',
        r'how can i make (.*)',
        r'give me recipe for (.*)',
        r'i want to make (.*)',
        r'how is (.*) made',
        r'how to cook (.*)',
        r'how to prepare (.*)'
    ]   
    recipe_name = None
    for pattern in recipe_query_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            recipe_name = match.group(1).strip()
            break
    print("recipe-name= ",recipe_name)
    if recipe_name:
        try:
            recipe_df = load_recipe_dataset()
            results, is_exact = search_recipe_by_name(recipe_df, recipe_name)
            print("results local dataset-> ",results)
            if not results.empty:
                # Format the results
                formatted_recipes = []
                for _, row in results.iterrows():
                    instructions = translate_if_hindi(row['TranslatedInstructions'])
                    formatted_recipes.append({
                        'title': row['TranslatedRecipeName'].title(),
                        'instructions': instructions,
                        'prep_time': row['PrepTimeInMins'],
                        'cook_time': row['CookTimeInMins'],
                        'total_time': row['TotalTimeInMins'],
                        'servings': row['Servings'],
                        'diet': row['Diet'],
                        'source': 'local_dataset'
                    })
                
                friendly_intro = f"Here are some recipes for {recipe_name}:"
                return {
                    "source": "local_dataset",
                    "text": friendly_intro,
                    "recipes": formatted_recipes,
                    "disease": None,
                    "chat_title": f"{recipe_name.title()} Recipes",
                    "followup": False
                }
        except Exception as e:
            print(f"Error searching local recipes: {e}")
            # Fall through to normal processing
            
    
    # Generate a title based on the user input
    title_prompt = f"""Generate a very short (2-4 word) title describing this recipe search request. 
    Focus on main ingredients or dietary needs. Examples:
    - "Chicken Recipes"
    - "Vegan Pasta"
    - "Diabetic-Friendly Meals"
    
    Request: "{user_input}"
    Title:"""
    
    try:
        title_response = model.generate_content(title_prompt)
        chat_title = title_response.text.strip().replace('"', '')
    except Exception as e:
        print(f"Error generating title: {e}")
        chat_title = f"Chat {datetime.now().strftime('%H:%M')}"
        
    
    # Extract disease and ingredients using Gemini
    disease, ingredients = extract_disease_and_ingredients(user_input)
    
    if not ingredients:  # Fallback if Gemini extraction fails
        ingredient_check_prompt = f"""
        You're an AI assistant for a recipe app.
        Does this message include specific food ingredients?
        Reply only with "yes" or "no".
        Message: "{user_input}"
        """
        response = model.generate_content(ingredient_check_prompt)
        decision = response.text.strip().lower()
        
        if decision != "yes":
            answer = model.generate_content(user_input).text
            return {
                "source": "gemini",
                "text": answer,
                "disease": disease
            }
    
    # Process ingredients and get recipes
    include, exclude, diet = extract_include_exclude_ingredients(user_input)
    recipe_data = search_recipes(include_ingredients=ingredients, exclude_ingredients=exclude, diet=diet)
    
    # print("recipe data->",recipe_data["recipes"])
    
    # print("include ingredients->",include)
    if recipe_data["status"] == "no_results":
        followup_prompt = f"""
        No recipes found with: {', '.join(include)}.
        Would you like me to try finding recipes using only these ingredients?
        Reply with 'yes' or 'no'.
        """
        return {
            "source": "spoonacular",
            "text": followup_prompt,
            "followup": True,
            "include_only": include,
            "disease": disease
        }
    
    safe_recipes=[]
    fallback_recipes=[]
    # friendly_intro=get_friendly_intro(ingredients,disease,bad_ingredients)
    if disease:
        matched_diseases, confidences = match_disease(disease)
        print("✅ Closest matches:")
        for d, score in zip(matched_diseases, confidences):
            print(f" - {d} (Confidence: {score:.2f})")

        bad_ingredients, safe_limits = merge_diseases(matched_diseases)
        print(f"\n🚫 Bad Ingredients: {bad_ingredients}")
        print(f"📊 Nutrient Safe Limits: {safe_limits}")
        print("🚀ingredients-->>>",ingredients)
        
        # 🔄 Expand bad ingredients using synonyms
        bad_ingredients = expand_bad_ingredients_with_synonyms(bad_ingredients, synonym_df)
        print(f"🔁 Expanded Bad Ingredients (with synonyms): {bad_ingredients}")
        print("bad ingredients->",bad_ingredients)
        
        # print("recipe data-->>",recipe_data)
        
        # recipe_data["recipes"] = filter_recipes(
        #     bad_ingredients, safe_limits, recipe_data["recipes"]
        # )
        friendly_intro=get_friendly_intro(ingredients,disease,bad_ingredients)
        result = get_safe_recipes(ingredients, bad_ingredients, safe_limits)
        safe_recipes = result["safe_recipes"]
        fallback_recipes = result["fallback_recipes"]
        # safe_recipes,fallback_recipes=get_safe_recipes(ingredients,bad_ingredients, safe_limits).value()
        # print("\nSafe recipes1-> ",safe_recipes)
        # print("fallback_recipes1-->>>",fallback_recipes)
        if not recipe_data["recipes"]:
            return {
                "source": "system",
                "text": f"No recipes found that meet the dietary restrictions for {disease}.",
                "disease": disease
            }
        else:
            print("hello") 
            response_data = {
                "source": "spoonacular",
                "recipes": safe_recipes if safe_recipes else [] ,
                "disease": disease,
                "friendly_intro":friendly_intro,
                "chat_title": chat_title,
                "followup": False,
                "fallback_recipes": fallback_recipes 
            }
            # print(f"\nFinal response data: {json.dumps(response_data, indent=2)}")
            return response_data
    else:
        friendly_intro=get_friendly_intro(ingredients,disease,bad_ingredients=None)
        print("hiii") 
        response_data = {
            "source": "spoonacular",
            "recipes": recipe_data.get("recipes", []),
            "disease": disease,
            "friendly_intro":friendly_intro,
            "chat_title": chat_title,
            "followup": False
        }
        print(f"\nFinal response data: {json.dumps(response_data, indent=2)}")
        return response_data


def get_friendly_intro(user_ingredients, user_conditions=None, bad_ingredients=None):
    condition_text = ""
    bad_ingredient_text = ""

    if user_conditions:
        condition_text = f"The user has the following health condition(s): {', '.join(user_conditions)}."

        if bad_ingredients:
            bad_ingredient_text = f"These ingredients might not be suitable: {', '.join(bad_ingredients)}. We've filtered the recipes to suit their needs."

    prompt = f"""
    A user gave me these ingredients: {', '.join(user_ingredients)}.
    {condition_text}
    {bad_ingredient_text}

    Respond with a friendly, short intro (1–2 sentences max) before I show them recipe suggestions.
    If a health condition is present, reassure the user and mention that unsuitable ingredients are filtered.
    Be cheerful and human-like. Do not be robotic. Add warmth and positivity.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini intro generation error:", str(e))
        return "Here are some healthy and delicious recipes tailored just for you!"




# Add these constants with your other paths
RECIPE_DATASET_PATH = "C:/Users/MANISHA/Downloads/RecipeChatbot/RecipeChatbot/IndianFoodDatasetXLS.xlsx"

# Initialize translator
translator = Translator()

def load_recipe_dataset():
    """Load and preprocess the recipe dataset"""
    df = pd.read_excel(RECIPE_DATASET_PATH, sheet_name='IndianFoodDataset8')
    
    # Remove unwanted columns
    cols_to_remove = ['RecipeName', 'Ingredients', 'Instructions', 'URL']
    df.drop(columns=[col for col in cols_to_remove if col in df.columns], inplace=True)
    
    # Normalize text
    df['TranslatedRecipeName'] = df['TranslatedRecipeName'].astype(str).str.strip().str.lower()
    df['TranslatedInstructions'] = df['TranslatedInstructions'].astype(str).str.strip()
    return df

def translate_if_hindi(text):
    """Translate text to English if it's in Hindi"""
    try:
        detected = translator.detect(text)
        if detected.lang == 'hi':
            translated = translator.translate(text, src='hi', dest='en')
            return translated.text
        return text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def search_recipe_by_name(df, query: str, top_n: int = 5):
    """Search recipes by name in the dataset"""
    query_cleaned = query.strip().lower()
    
    # Step 1: Exact containment
    exact_matches = df[df['TranslatedRecipeName'].str.contains(query_cleaned, case=False, na=False)]
    if not exact_matches.empty:
        return exact_matches.head(top_n), True
    
    # Step 2: Partial word match fallback
    words = query_cleaned.split()
    partial_matches = df[df['TranslatedRecipeName'].apply(
        lambda name: any(word in name for word in words)
    )]
    return partial_matches.head(top_n), False