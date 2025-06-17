import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# ---------------------- Data Preparation ----------------------
def load_and_preprocess_user_data(user_csv_path):
    df = pd.read_csv(user_csv_path)
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    if 'height(m)' in df.columns:
        df['height(m)'] = df['height(m)'] * 100
        df.rename(columns={'height(m)': 'Height'}, inplace=True)
        if 'height(m)' in numeric_cols:
            numeric_cols.remove('height(m)')
        numeric_cols.append('Height')
    elif 'Height' in df.columns:
        if 'Height' not in numeric_cols:
            numeric_cols.append('Height')
    else:
        raise ValueError("Height column not found in expected format.")

    df[numeric_cols] = df[numeric_cols].round(0).astype(int)
    return df


def capitalize_first_letters(input_string):
    """Capitalize first letter of each word and make rest lowercase"""
    if pd.isna(input_string) or input_string == '':
        return input_string
    return ' '.join(word.capitalize() for word in input_string.split())


def encode_gender(df):
    le = LabelEncoder()
    le.fit(['Male', 'Female'])
    if df['gender'].dtype == 'object':
        df['gender'] = le.transform(df['gender'])
    return df, le

# ---------------------- Model Training ----------------------
def train_macro_models(df, feature_cols, target_cols):
    models = {}
    X = df[feature_cols]

    for target in target_cols:
        if target in df.columns:
            y = df[target]
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            models[target] = model
        else:
            print(f"Error: '{target}' not found in dataset.")
    return models

# ---------------------- Macro Prediction ----------------------
def predict_macros(models, user_input, target_cols):
    predictions = {
        target: round(models[target].predict(user_input)[0])
        for target in target_cols
    }
    predictions['Calories'] = predictions.pop('calories_to_maintain_weight')

    total_calories = predictions['Calories']
    predictions['Protein'] = round((total_calories * 0.30) / 4)
    predictions['Carbohydrates'] = round((total_calories * 0.40) / 4)
    predictions['Fat'] = round((total_calories * 0.30) / 9)

    return predictions

# ---------------------- Recipe Filtering ----------------------
def get_recipe_categories():
    return {
        'Breakfast': ['Breakfast', 'Brunch', 'Smoothies', 'Oatmeal',        'Scones', 'Quick Breads', 'Breads', 'Yeast Breads', 'Cheese', 'Fruit', 'Apple', 'Pineapple', 'Citrus', 'Oranges', 'Melons'],
        
        'Lunch': ['Lunch/Snacks', 'Vegetable', 'Chicken Breast', 'Potato', 'Rice', 'Salad Dressings', 'Grains','Pasta Shells', 'Penne', 'Cheese', 'Curries', 'Corn', 'Cauliflower', 'Soy/Tofu', 'Healthy', 'Weeknight','Kid Friendly'],
        
        'Snack': ['Dessert', 'Bar Cookie', 'Drop Cookies', 'Candy', 'Frozen Desserts', 'Cheesecake', 'Pie', 'Gelatin', 'Tarts', 'Spreads', 'Nuts', 'Punch Beverage', 'Shakes', 'Beverages', 'Smoothies', 'Jellies', 'Spicy', 'Fruit', 'Berries', 'Mango', 'Cherries'],
        
        'Dinner': ['One Dish Meal', 'Chicken', 'Pork', 'Meat', 'Lamb/Sheep', 'Stew', 'Curries', 'Poultry', 'Beans', 'Spaghetti', 'Savory Pies', 'Yam/Sweet Potato', 'Vegetable', 'Pasta', 'Rice', 'Whole Chicken', 'Whole Turkey', 'Chicken Thigh & Leg', 'Steak', 'Veal', 'Roast Beef', 'Meatloaf', 'Tuna', 'Lentil']
    }


def filter_recipes_by_type(df, meal_type, macro_targets, diet_pref, category_groups):
    categories = category_groups[meal_type]
     # Ensure diet_pref is properly capitalized for matching
    diet_pref = capitalize_first_letters(diet_pref)
    subset = df[
        (df['RecipeCategory'].isin(categories)) &
        (df['Dietary Type'].str.lower() == diet_pref.lower())
    ].dropna(subset=['RecipeId']).copy()

    for macro in ['Calories', 'Protein', 'Carbohydrates']:
        if macro in macro_targets and macro in subset.columns:
            target = macro_targets[macro] / 4
            subset = subset[
                (subset[macro] >= target * 0.9) &
                (subset[macro] <= target * 1.1)
            ]

    if subset.empty:
        fallback = df[
            (df['RecipeCategory'].isin(categories)) &
            (df['Dietary Type'].str.lower() == diet_pref.lower())
        ].dropna(subset=['RecipeId']).copy()

        if fallback.empty:
            print(f"Warning: No recipes found for {meal_type} with preference {diet_pref}")
            return pd.DataFrame()
        print(f"Warning: Filtered subset for {meal_type} is empty. Using fallback.")
        return fallback.reset_index(drop=True)

    return subset.reset_index(drop=True)

# ---------------------- Weekly Plan Generator ----------------------
def generate_weekly_plan(recipes_df, daily_macros, diet_pref, category_groups):
    plan = []

    for day in range(7):
        day_plan = {'Day': f'Day {day + 1}'}
        daily_total = {'Calories': 0, 'Protein': 0, 'Carbohydrates': 0, 'Fat': 0}

        for meal in ['Breakfast', 'Lunch', 'Dinner', 'Snack']:
            options = filter_recipes_by_type(recipes_df, meal, daily_macros, diet_pref, category_groups)
            if options.empty:
                chosen = {'Name': 'No Match', 'Calories': 0, 'Protein': 0, 'Carbohydrates': 0, 'Fat': 0}
            else:
                chosen_row = options.sample(1).iloc[0]
                chosen = {
                    'Name': chosen_row.get('Name', 'Unknown Recipe'),
                    'Calories': chosen_row.get('Calories', 0),
                    'Protein': chosen_row.get('Protein', 0),
                    'Carbohydrates': chosen_row.get('Carbohydrates', 0),
                    'Fat': chosen_row.get('Fat', 0),
                }

            day_plan[meal] = chosen['Name']
            for macro in daily_total:
                day_plan[f"{meal}_{macro}"] = round(chosen.get(macro, 0))
                daily_total[macro] += chosen.get(macro, 0)

        for macro in daily_total:
            day_plan[f'Total {macro}'] = round(daily_total[macro])

        plan.append(day_plan)

    return pd.DataFrame(plan)



def map_user_input(user_input_dict, le_gender):
    processed_input = {
        'Ages': user_input_dict['Ages'],
        'Gender': capitalize_first_letters(user_input_dict['Gender']),
        'Height': user_input_dict['Height'],
        'Weight': user_input_dict['Weight'],
        'Dietary Preference': capitalize_first_letters(user_input_dict['Dietary Preference']),
        'Activity Level': capitalize_first_letters(user_input_dict['Activity Level'])
    }
    return {
        'age': int(processed_input['Ages']),
        'gender': le_gender.transform([processed_input['Gender']])[0],
        'Height': float(processed_input['Height']),
        'weight(kg)': int(processed_input['Weight']),
        'Dietary Preference': processed_input['Dietary Preference'],
        'Activity Level': processed_input['Activity Level']
    }


# ---------------------- Main Script ----------------------
def get_diet_chart(user_input_dict):
    # Load and process user data
    user_df = load_and_preprocess_user_data('Dataset (2).csv')
    user_df, le_gender = encode_gender(user_df)

    feature_cols = ['age', 'gender', 'Height', 'weight(kg)']
    target_cols = ['calories_to_maintain_weight']

    macro_models = train_macro_models(user_df, feature_cols, target_cols)

    # Map and preprocess new user input
    processed_input = map_user_input(user_input_dict, le_gender)
    user_input_array = np.array([[processed_input[c] for c in feature_cols]])

    # Predict macros
    daily_macros = predict_macros(macro_models, user_input_array, target_cols)

    print("\n🔢 Predicted Daily Macronutrient Needs:")
    print(daily_macros)

    # Load recipes
    recipes_df = pd.read_csv('cleaned_dataset_new.csv')
    recipes_df.rename(columns={'CarbohydrateContent': 'Carbohydrates', 'ProteinContent': 'Protein'}, inplace=True)

    # Generate meal plan
    category_groups = get_recipe_categories()
    weekly_plan_df = generate_weekly_plan(
        recipes_df,
        daily_macros,
        processed_input['Dietary Preference'],
        category_groups
    )

    # print("\n📅 Weekly Meal Plan:")
    # print(weekly_plan_df.to_string(index=False))

    weekly_plan_df.to_csv("weekly_meal_plan_no_disease.csv", index=False)
    return daily_macros, weekly_plan_df

# Run the script
if __name__ == "__main__":
    get_diet_chart()
