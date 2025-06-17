import pandas as pd
import numpy as np
import random
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

# Load datasets
meals_df = pd.read_csv("detailed_meals_macros_.csv")
recipes_df = pd.read_csv("cleaned_dataset_new.csv")

# Preprocess and train once
feature_cols = ['Ages', 'Gender', 'Height', 'Weight', 'Activity Level', 'Dietary Preference', 'Disease']
target_macros = ['Daily Calorie Target', 'Protein', 'Carbohydrates']

label_encoders = {}
data = meals_df.copy()
data['Disease'] = data['Disease'].fillna('').str.strip()
data = data.assign(Disease=data['Disease'].str.split(',')).explode('Disease')
data['Disease'] = data['Disease'].str.strip()

# Label Encoding
for col in ['Gender', 'Activity Level', 'Dietary Preference', 'Disease']:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col])
    label_encoders[col] = le

X = data[feature_cols]

# Train models
macro_models = {}
for macro in target_macros:
    y = data[macro]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    macro_models[macro] = model

# Category groups
category_groups = {
    'Breakfast': ['Breakfast', 'Brunch', 'Smoothies', 'Oatmeal', 'Scones', 'Quick Breads', 'Breads', 'Yeast Breads',
                  'Cheese', 'Fruit', 'Apple', 'Pineapple', 'Citrus', 'Oranges', 'Melons'],
    'Lunch': ['Lunch/Snacks', 'Vegetable', 'Chicken Breast', 'Potato', 'Rice', 'Salad Dressings', 'Grains',
              'Pasta Shells', 'Penne', 'Cheese', 'Curries', 'Corn', 'Cauliflower', 'Soy/Tofu', 'Healthy', 'Weeknight',
              'Kid Friendly'],
    'Snack': ['Dessert', 'Bar Cookie', 'Drop Cookies', 'Candy', 'Frozen Desserts', 'Cheesecake', 'Pie', 'Gelatin',
              'Tarts', 'Spreads', 'Nuts', 'Punch Beverage', 'Shakes', 'Beverages', 'Smoothies', 'Jellies', 'Spicy',
              'Fruit', 'Berries', 'Mango', 'Cherries'],
    'Dinner': ['One Dish Meal', 'Chicken', 'Pork', 'Meat', 'Lamb/Sheep', 'Stew', 'Curries', 'Poultry', 'Beans',
               'Spaghetti', 'Savory Pies', 'Yam/Sweet Potato', 'Vegetable', 'Pasta', 'Rice', 'Whole Chicken',
               'Whole Turkey', 'Chicken Thigh & Leg', 'Steak', 'Veal', 'Roast Beef', 'Meatloaf', 'Tuna', 'Lentil']
}

# Clean recipe column names
recipes_df.rename(columns={
    'CarbohydrateContent': 'Carbohydrates',
    'ProteinContent': 'Protein',
}, inplace=True)

def get_recipes_by_type(meal_type, macro_targets, diet_pref):
    categories = category_groups[meal_type]
    subset = recipes_df[
        (recipes_df['RecipeCategory'].isin(categories)) &
        (recipes_df['Dietary Type'].str.lower() == diet_pref.lower())
    ].copy()

    subset = subset.dropna(subset=['RecipeId'])

    macro_mapping = {
        'Calories': 'Calories',
        'Protein': 'Protein',
        'Carbohydrates': 'Carbohydrates',
    }

    for macro, recipe_col in macro_mapping.items():
        target = macro_targets[macro] / 4
        if recipe_col in subset.columns:
            subset = subset[
                (subset[recipe_col] >= target * 0.9) &
                (subset[recipe_col] <= target * 1.1)
            ]

    if subset.empty:
        fallback_subset = recipes_df[
            (recipes_df['RecipeCategory'].isin(categories)) &
            (recipes_df['Dietary Type'].str.lower() == diet_pref.lower())
        ].copy().dropna(subset=['RecipeId'])

        return fallback_subset.reset_index(drop=True)

    return subset.reset_index(drop=True)


def capitalize_first_letters(input_string):
    """Capitalize first letter of each word and make rest lowercase"""
    return ' '.join(word.capitalize() for word in input_string.split())

def generate_diet_plan_disease(user_input_dict):
    # Process string inputs to capitalize first letters
    processed_input = {
        'Ages': user_input_dict['Ages'],
        'Gender': capitalize_first_letters(user_input_dict['Gender']),
        'Height': user_input_dict['Height'],
        'Weight': user_input_dict['Weight'],
        'Activity Level': capitalize_first_letters(user_input_dict['Activity Level']),
        'Dietary Preference': capitalize_first_letters(user_input_dict['Dietary Preference']),
        'Disease': capitalize_first_letters(user_input_dict['Disease'])
    }
    
    # Match disease label from encoder
    disease_labels = label_encoders['Disease'].classes_
    user_disease = processed_input['Disease']
    matching_label = next((i for i, d in enumerate(disease_labels) if user_disease.lower() in d.lower()), 0)

    new_user = {
        'Ages': int(processed_input['Ages']),
        'Gender': label_encoders['Gender'].transform([processed_input['Gender']])[0],
        'Height': float(processed_input['Height']),
        'Weight': float(processed_input['Weight']),
        'Activity Level': label_encoders['Activity Level'].transform([processed_input['Activity Level']])[0],
        'Dietary Preference': label_encoders['Dietary Preference'].transform([processed_input['Dietary Preference']])[0],
        'Disease': matching_label
    }

    user_input = np.array([list(new_user.values())])
    daily_macros = {macro: round(macro_models[macro].predict(user_input)[0]) for macro in target_macros}
    daily_macros['Calories'] = daily_macros.pop('Daily Calorie Target')

    diet_pref_value = new_user['Dietary Preference']
    diet_pref_label = label_encoders['Dietary Preference'].inverse_transform([diet_pref_value])[0]

    weekly_plan = []
    for day in range(7):
        day_plan = {'Day': f'Day {day + 1}'}
        daily_total = {'Calories': 0, 'Protein': 0, 'Carbohydrates': 0}

        for meal in ['Breakfast', 'Lunch', 'Dinner', 'Snack']:
            options = get_recipes_by_type(meal, daily_macros, diet_pref_label)
            if options.empty:
                chosen = {'Name': 'No Match', 'Calories': 0, 'Protein': 0, 'Carbohydrates': 0}
            else:
                chosen_row = options.sample(1).iloc[0]
                chosen = {
                    'Name': chosen_row.get('Name', 'Unknown Recipe'),
                    'Calories': chosen_row.get('Calories', 0),
                    'Protein': chosen_row.get('Protein', 0),
                    'Carbohydrates': chosen_row.get('Carbohydrates', 0),
                }

            day_plan[meal] = chosen['Name']
            for macro in daily_total:
                day_plan[f"{meal}_{macro}"] = round(chosen.get(macro, 0))
                daily_total[macro] += chosen.get(macro, 0)

        for macro in daily_total:
            day_plan[f'Total {macro}'] = round(daily_total[macro])

        weekly_plan.append(day_plan)

    weekly_plan_df = pd.DataFrame(weekly_plan)

    return daily_macros, weekly_plan_df
