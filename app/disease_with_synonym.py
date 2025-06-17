import pandas as pd

# Load your dataset
df = pd.read_csv("modified_disease_nutrient_dataset_updated.csv")

# Function to generate basic synonyms
def generate_basic_synonyms(disease_name):
    name = disease_name.lower()
    synonyms = set()

    if "kidney" in name:
        synonyms.update(["renal disease", "kidney failure", "renal failure"])
    if "liver" in name:
        synonyms.update(["hepatic disease", "liver condition", "hepatic disorder"])
    if "heart" in name or "coronary" in name:
        synonyms.update(["cardiac disease", "cardiovascular disease", "heart condition"])
    if "diabetes" in name:
        synonyms.update(["diabetes mellitus", "high blood sugar", "hyperglycemia"])
    if "hypertension" in name or "blood pressure" in name:
        synonyms.update(["high blood pressure", "HTN", "elevated blood pressure"])
    if "anemia" in name:
        synonyms.update(["iron deficiency", "low hemoglobin", "hematologic disorder"])
    if "asthma" in name:
        synonyms.update(["bronchial asthma", "respiratory condition", "airway inflammation"])
    if "osteoporosis" in name:
        synonyms.update(["bone loss", "brittle bones", "low bone density"])
    if "thyroid" in name:
        synonyms.update(["thyroid disorder", "thyroid imbalance", "hyperthyroidism", "hypothyroidism"])
    if "celiac" in name:
        synonyms.update(["gluten intolerance", "celiac sprue"])
    if "syndrome" in name:
        synonyms.add("metabolic disorder")
    if "arthritis" in name:
        synonyms.update(["joint inflammation", "joint disease"])
    if "disease" in name:
        synonyms.add(name.replace("disease", "condition"))

    # Always include the original name for context
    synonyms.add(name)
    return ', '.join(sorted(synonyms))

# Add the Synonyms column
df['Synonyms'] = df['Disease Name'].apply(generate_basic_synonyms)

# Save to a new CSV
df.to_csv("modified_disease_nutrient_dataset_with_synonyms.csv", index=False)

print("✅ Synonyms added and saved to 'modified_disease_nutrient_dataset_with_synonyms.csv'")
