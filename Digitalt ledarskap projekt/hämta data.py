import io
import pandas as pd
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RiksdagAnalys/1.0"
}

# -------------------------------------------------------------
# 1. Hämta och läs in voteringar (CSV utan rubrikrad)
# -------------------------------------------------------------
voteringar_url = "https://data.riksdagen.se/dataset/votering/votering-202324.csv.zip"
print("1. Laddar ner voteringsdata...")
res_vot = requests.get(voteringar_url, headers=headers)
res_vot.raise_for_status()

# Riksdagens voteringsfiler saknar header. Kolumnordningen är känd:
kolumner_vot = [
    "rm", "beteckning", "votering_id", "punkt", "namn", 
    "intressent_id", "parti", "valkrets", "rost", "avser", 
    "votering", "bankod", "fornamn", "efternamn", "kon", "fodd"
]

df_vot = pd.read_csv(
    io.BytesIO(res_vot.content),
    compression="zip",
    sep=None,
    engine="python",
    encoding="utf-8-sig",
    header=None,
    names=kolumner_vot
)
print(f"   -> {len(df_vot):,} voteringsrader inlästa.")

# -------------------------------------------------------------
# 2. Hämta betänkanderubriker direkt via API:et
# -------------------------------------------------------------
print("2. Hämtar titlar för betänkanden via API...")
dok_api_url = "https://data.riksdagen.se/dokumentlista/"
params = {
    "rm": "2023/24",
    "doktyp": "bet",
    "utformat": "json",
    "sz": 500  # Ett riksmöte har sällan fler än 300 betänkanden
}

res_dok = requests.get(dok_api_url, params=params, headers=headers)
res_dok.raise_for_status()
dok_data = res_dok.json()

dokument_list = dok_data.get("dokumentlista", {}).get("dokument", [])
bet_titlar = []
for doc in dokument_list:
    bet_titlar.append({
        "rm": doc.get("rm"),
        "beteckning": doc.get("beteckning"),
        "titel": doc.get("titel"),
        "notisrubrik": doc.get("notisrubrik", "")
    })

df_bet = pd.DataFrame(bet_titlar).drop_duplicates(subset=["rm", "beteckning"])
print(f"   -> {len(df_bet)} betänkanden hämtade.")

# -------------------------------------------------------------
# 3. Aggregera partiernas majoritetsröst per ärende och punkt
# -------------------------------------------------------------
print("3. Bygger partiernas röstmatris...")
parti_roster = (
    df_vot.groupby(["rm", "beteckning", "punkt", "parti"])["rost"]
    .agg(lambda x: x.mode()[0] if not x.empty else "Frånvarande")
    .unstack(level="parti")
    .reset_index()
)

# -------------------------------------------------------------
# 4. Slå ihop och visa resultatet
# -------------------------------------------------------------
resultat = pd.merge(parti_roster, df_bet, on=["rm", "beteckning"], how="left")

# Ordna kolumner snyggt
partier = [p for p in ["S", "M", "SD", "V", "C", "KD", "MP", "L"] if p in resultat.columns]
kolumner = ["beteckning", "punkt", "titel"] + partier

print("\n--- RESULTAT (Utdrag ur riksmötet 2023/24) ---")
print(resultat[kolumner].dropna(subset=["titel"]).head(15).to_string(index=False))

# Exportera till Excel eller CSV
filnamn = "partiernas_roster_202324.csv"
resultat[kolumner].to_csv(filnamn, index=False, encoding="utf-8-sig")
print(f"\nKlart! Tabellen har även sparats lokalt till '{filnamn}'.")