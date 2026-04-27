# 🤖 Bot Telegram - Chasseur de Deals

Bot Telegram qui surveille automatiquement les meilleures offres sur :
- 🟦 **Dealabs**
- 🔍 **Google Shopping**
- 💰 **Idealo**

## 📋 Critères de sélection

✅ **Inclus :**
- Réductions de -50% et plus
- Produits neufs uniquement
- Toutes catégories (sauf mode)

❌ **Exclus :**
- Amazon
- Mode et vêtements
- Produits digitaux (ebooks, codes, cartes cadeaux)

## 🚀 Installation

### Option 1 : Sur votre ordinateur (test)

1. **Installez Python 3.9+** (si pas déjà fait)
   - Windows : https://www.python.org/downloads/
   - Mac : déjà installé
   - Linux : `sudo apt install python3 python3-pip`

2. **Téléchargez les fichiers**
   ```bash
   # Créez un dossier
   mkdir deals-bot
   cd deals-bot
   
   # Copiez les 3 fichiers :
   # - deals_bot.py
   # - requirements.txt
   # - start.sh
   ```

3. **Lancez le bot**
   ```bash
   # Sur Mac/Linux
   chmod +x start.sh
   ./start.sh
   
   # Sur Windows
   pip install -r requirements.txt
   python deals_bot.py
   ```

### Option 2 : Sur un serveur 24/7 (recommandé)

#### A. **Railway.app** (Gratuit pour commencer)

1. Créez un compte sur https://railway.app
2. Cliquez sur "New Project" → "Deploy from GitHub repo"
3. Connectez votre dépôt GitHub
4. Railway détecte automatiquement Python
5. Le bot démarre automatiquement !

#### B. **Render.com** (Gratuit)

1. Créez un compte sur https://render.com
2. Cliquez sur "New" → "Background Worker"
3. Connectez votre dépôt GitHub
4. Build Command : `pip install -r requirements.txt`
5. Start Command : `python deals_bot.py`

#### C. **DigitalOcean** (~5€/mois)

Plus technique mais plus fiable :
```bash
# Sur le serveur
git clone VOTRE_REPO
cd deals-bot
pip3 install -r requirements.txt
nohup python3 deals_bot.py &
```

## 📝 Configuration

Vos identifiants sont déjà configurés dans `deals_bot.py` :
- Token Bot : `8339957915:AAHf3v09yGrBWzmVXR32CIhIFMCKKdM4yHw`
- Chat ID : `857240393`

**⚠️ SÉCURITÉ :**
Pour plus de sécurité, utilisez des variables d'environnement :

```python
# Au lieu de :
TELEGRAM_TOKEN = "8339957915:..."

# Utilisez :
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
```

Puis définissez-les sur votre plateforme d'hébergement.

## 🔧 Personnalisation

### Changer la fréquence de vérification :
```python
CHECK_INTERVAL = 900  # 15 minutes (en secondes)
# 600 = 10 min
# 1800 = 30 min
# 3600 = 1 heure
```

### Ajuster le seuil de réduction :
```python
if deal['discount'] >= 50:  # Changez 50 par le % minimum souhaité
```

### Ajouter des exclusions :
```python
EXCLUDED_KEYWORDS = [
    # Ajoutez vos mots-clés ici
    'mot-à-exclure',
]
```

## 📊 État actuel

🟡 **Version PROTOTYPE**

Le code contient des placeholders pour :
- Scraping Dealabs (nécessite BeautifulSoup)
- API Google Shopping (nécessite clé API)
- Scraping Idealo (nécessite configuration)

### Prochaines étapes pour le rendre opérationnel :

1. **Implémenter le vrai scraping Dealabs**
2. **Configurer l'API Google Shopping**
3. **Ajouter le scraping Idealo**
4. **Gérer le stockage des deals déjà vus**

## 🆘 Support

### Le bot ne démarre pas ?
```bash
# Vérifiez Python
python --version  # Doit être 3.9+

# Réinstallez les dépendances
pip install --upgrade -r requirements.txt
```

### Pas de messages reçus ?
1. Vérifiez que vous avez bien démarré votre bot (@BotFather)
2. Envoyez `/start` à votre bot
3. Vérifiez les logs pour voir les erreurs

### Trop de messages ?
Augmentez `CHECK_INTERVAL` dans le code.

## 📞 Contact

Pour toute question, vérifiez les logs du bot ou consultez la documentation Telegram Bot API.
