import os
import time
import requests
from datetime import datetime
import re
from bs4 import BeautifulSoup
import json

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = 900  # 15 minutes

# DEBUG
print(f"🔧 DEBUG - Token chargé: {TELEGRAM_TOKEN[:20]}..." if TELEGRAM_TOKEN else "❌ Token VIDE")
print(f"🔧 DEBUG - Chat ID: {CHAT_ID}")

# Exclusions
EXCLUDED_KEYWORDS = [
    'vêtement', 'vetement', 'chaussure', 'robe', 'pantalon', 'jean', 
    'chemise', 't-shirt', 'tshirt', 'pull', 'manteau', 'veste', 'blouson',
    'basket', 'sneaker', 'chaussette', 'lingerie', 'sous-vêtement',
    'accessoire mode', 'sac à main', 'bijou', 'montre fashion',
    'polo', 'short', 'maillot', 'casquette', 'bonnet', 'écharpe',
    'sweat', 'hoodie', 'jogging', 'legging', 'combinaison', 'kimono'
]

AMAZON_KEYWORDS = ['amazon.fr', 'amazon.com', 'amzn', 'amazon']

DIGITAL_KEYWORDS = [
    'dématérialisé', 'digital', 'téléchargement', 'download',
    'code psn', 'code steam', 'carte cadeau', 'gift card',
    'ebook', 'e-book', 'kindle', 'abonnement', 'streaming',
    'jeu vidéo pc', 'clé cd', 'code activation', 'carte prépayée'
]

def send_telegram_message(message):
    """Envoie un message via Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Erreur envoi Telegram: {e}")
        return None

def extract_discount(text):
    """Extrait le pourcentage de réduction"""
    matches = re.findall(r'-(\d+)%', text)
    if matches:
        return max([int(m) for m in matches])
    return 0

def extract_price(text):
    """Extrait le prix d'un texte"""
    matches = re.findall(r'(\d+[,.]?\d*)\s*€', text)
    if matches:
        return matches[0] + '€'
    return "Prix non disponible"

def is_excluded(title, description="", merchant=""):
    """Vérifie si le deal doit être exclu"""
    text = (title + " " + description + " " + merchant).lower()
    
    # Exclure mode
    for keyword in EXCLUDED_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    # Exclure Amazon
    for keyword in AMAZON_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    # Exclure digitaux
    for keyword in DIGITAL_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    return False

def check_dealabs_all():
    """Scrape la page "Tous" de Dealabs"""
    deals = []
    
    try:
        # Page principale "Tous les deals"
        url = "https://www.dealabs.com/nouveaux"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Referer': 'https://www.dealabs.com/'
        }
        
        print(f"   📡 URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher tous les articles de deals (plusieurs sélecteurs possibles)
            deal_containers = []
            
            # Méthode 1: Chercher par class contenant "thread"
            deal_containers.extend(soup.find_all('article', class_=lambda x: x and 'thread' in str(x).lower()))
            
            # Méthode 2: Chercher par data-handler
            if not deal_containers:
                deal_containers.extend(soup.find_all('article', attrs={'data-handler': True}))
            
            # Méthode 3: Tous les articles
            if not deal_containers:
                deal_containers.extend(soup.find_all('article'))
            
            print(f"   📦 {len(deal_containers)} containers trouvés")
            
            for item in deal_containers[:30]:  # Limiter à 30 deals
                try:
                    # Extraire tout le texte de l'article
                    full_text = item.get_text()
                    
                    # Vérifier s'il y a une réduction
                    discount = extract_discount(full_text)
                    
                    if discount < 50:
                        continue
                    
                    # Extraire le titre
                    title = ""
                    title_candidates = [
                        item.find('strong'),
                        item.find('a', class_=lambda x: x and 'title' in str(x).lower()),
                        item.find('span', class_=lambda x: x and 'title' in str(x).lower()),
                        item.find('h2'),
                        item.find('h3')
                    ]
                    
                    for candidate in title_candidates:
                        if candidate:
                            title = candidate.get_text(strip=True)
                            if len(title) > 10:  # Titre valide
                                break
                    
                    if not title:
                        continue
                    
                    # Extraire l'URL
                    link = item.find('a', href=True)
                    url_deal = ""
                    if link:
                        url_deal = link['href']
                        if url_deal and not url_deal.startswith('http'):
                            url_deal = 'https://www.dealabs.com' + url_deal
                    
                    if not url_deal:
                        continue
                    
                    # Extraire le prix
                    price = extract_price(full_text)
                    
                    # Extraire le marchand
                    merchant = ""
                    merchant_elem = item.find('span', class_=lambda x: x and 'merchant' in str(x).lower())
                    if merchant_elem:
                        merchant = merchant_elem.get_text(strip=True)
                    
                    # Si pas de marchand trouvé, chercher dans le texte
                    if not merchant:
                        common_merchants = ['Amazon', 'Cdiscount', 'Fnac', 'Darty', 'Boulanger', 'Leclerc', 'Carrefour', 'Auchan', 'Lidl']
                        for m in common_merchants:
                            if m.lower() in full_text.lower():
                                merchant = m
                                break
                    
                    # Vérifier exclusions
                    if is_excluded(title, full_text, merchant):
                        continue
                    
                    # Ajouter le deal
                    deals.append({
                        'title': title[:200],
                        'price': price,
                        'old_price': '',
                        'discount': discount,
                        'url': url_deal,
                        'source': 'Dealabs',
                        'merchant': merchant
                    })
                    
                except Exception as e:
                    continue
        
    except Exception as e:
        print(f"   ❌ Erreur Dealabs: {e}")
    
    return deals

def check_pepper_deals():
    """Scrape Pepper.com (backup)"""
    deals = []
    
    try:
        url = "https://www.pepper.com/nouveaux"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            deal_items = soup.find_all('article')[:20]
            
            for item in deal_items:
                try:
                    full_text = item.get_text()
                    discount = extract_discount(full_text)
                    
                    if discount < 50:
                        continue
                    
                    title_elem = item.find('strong')
                    if not title_elem:
                        title_elem = item.find('a')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        if is_excluded(title, full_text):
                            continue
                        
                        link = item.find('a', href=True)
                        url_deal = link['href'] if link else ""
                        
                        price = extract_price(full_text)
                        
                        deals.append({
                            'title': title[:200],
                            'price': price,
                            'old_price': '',
                            'discount': discount,
                            'url': url_deal,
                            'source': 'Pepper',
                            'merchant': ''
                        })
                except:
                    continue
    
    except Exception as e:
        print(f"   ❌ Erreur Pepper: {e}")
    
    return deals

def format_deal_message(deal):
    """Formate un deal pour Telegram"""
    merchant_info = f"\n🏪 Marchand: {deal['merchant']}" if deal.get('merchant') else ""
    
    message = f"""
🔥 <b>SUPER DEAL -{deal['discount']}%</b> 🔥

📦 {deal['title']}

💰 <b>{deal['price']}</b>{merchant_info}

🌐 Source: {deal['source']}
🔗 <a href="{deal['url']}">👉 VOIR L'OFFRE</a>

⏰ {datetime.now().strftime('%d/%m/%Y à %H:%M')}
"""
    return message.strip()

def main():
    """Fonction principale"""
    print("=" * 50)
    print("🤖 BOT DEALS TELEGRAM - DÉMARRÉ")
    print("=" * 50)
    print(f"⏱️  Intervalle: {CHECK_INTERVAL//60} minutes")
    print(f"💰 Réduction min: -50%")
    print(f"🚫 Exclusions: Mode, Amazon, Digital")
    print("=" * 50)
    
    # Message de démarrage
    print("🔧 Test envoi message Telegram...")
    test_result = send_telegram_message("🔧 TEST - Le bot démarre...")
    print(f"Résultat: {test_result}")
    
    send_telegram_message(
        "✅ <b>Bot Chasseur de Deals ACTIVÉ !</b>\n\n"
        "🔍 Surveillance active sur:\n"
        "  • Dealabs (page TOUS)\n"
        "  • Pepper (page TOUS)\n\n"
        "💰 Seuil: -50% minimum\n"
        "🚫 Exclus: Mode • Amazon • Digital\n\n"
        "⏰ Vous recevrez les deals en temps réel !"
    )
    
    seen_deals = set()
    check_count = 0
    
    while True:
        try:
            check_count += 1
            print(f"\n{'='*50}")
            print(f"🔍 CHECK #{check_count} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"{'='*50}")
            
            all_deals = []
            
            # Vérifier Dealabs (page TOUS)
            print("📡 Scraping Dealabs (page TOUS)...")
            dealabs_deals = check_dealabs_all()
            all_deals.extend(dealabs_deals)
            print(f"   ✓ {len(dealabs_deals)} deals trouvés")
            
            time.sleep(3)
            
            # Vérifier Pepper (backup)
            print("📡 Scraping Pepper...")
            pepper_deals = check_pepper_deals()
            all_deals.extend(pepper_deals)
            print(f"   ✓ {len(pepper_deals)} deals trouvés")
            
            # Filtrer nouveaux deals
            new_deals = []
            for deal in all_deals:
                deal_id = deal['url'] + str(deal['discount'])
                if deal_id not in seen_deals:
                    new_deals.append(deal)
                    seen_deals.add(deal_id)
            
            print(f"\n📊 Résultat: {len(new_deals)} nouveaux deals")
            
            # Envoyer les nouveaux deals
            if new_deals:
                print(f"\n📤 Envoi de {len(new_deals)} deals...")
                for i, deal in enumerate(new_deals, 1):
                    message = format_deal_message(deal)
                    result = send_telegram_message(message)
                    
                    if result and result.get('ok'):
                        print(f"   ✅ [{i}/{len(new_deals)}] {deal['title'][:50]}... (-{deal['discount']}%)")
                    else:
                        print(f"   ❌ [{i}/{len(new_deals)}] Erreur envoi")
                    
                    time.sleep(2)  # Anti-spam
                
                print(f"\n🎉 {len(new_deals)} deals envoyés avec succès !")
            else:
                print("😴 Aucun nouveau deal pour le moment")
            
            # Nettoyage mémoire
            if len(seen_deals) > 1000:
                seen_deals.clear()
                print("🧹 Cache nettoyé")
            
            # Attente
            print(f"\n⏳ Prochaine vérification dans {CHECK_INTERVAL//60} minutes...")
            print(f"{'='*50}\n")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n" + "="*50)
            print("⛔ ARRÊT DU BOT DEMANDÉ")
            print("="*50)
            send_telegram_message("⛔ <b>Bot Deals arrêté</b>\n\nÀ bientôt ! 👋")
            break
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            print("⏳ Nouvelle tentative dans 60 secondes...")
            time.sleep(60)

if __name__ == "__main__":
    main()
