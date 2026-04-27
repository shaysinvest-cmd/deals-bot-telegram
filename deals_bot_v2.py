import os
import time
import requests
from datetime import datetime
import re
from bs4 import BeautifulSoup
import json

# Configuration
TELEGRAM_TOKEN = "8339957915:AAHf3v09yGrBWzmVXR32CIhIFMCKKdM4yHw"
CHAT_ID = "857240393"
CHECK_INTERVAL = 900  # 15 minutes

# Exclusions
EXCLUDED_KEYWORDS = [
    'vêtement', 'vetement', 'chaussure', 'robe', 'pantalon', 'jean', 
    'chemise', 't-shirt', 'tshirt', 'pull', 'manteau', 'veste', 'blouson',
    'basket', 'sneaker', 'chaussette', 'lingerie', 'sous-vêtement',
    'accessoire mode', 'sac à main', 'bijou', 'montre fashion',
    'polo', 'short', 'maillot', 'casquette', 'bonnet', 'écharpe'
]

AMAZON_KEYWORDS = ['amazon.fr', 'amazon.com', 'amzn', 'amazon']

DIGITAL_KEYWORDS = [
    'dématérialisé', 'digital', 'téléchargement', 'download',
    'code psn', 'code steam', 'carte cadeau', 'gift card',
    'ebook', 'e-book', 'kindle', 'abonnement', 'streaming',
    'jeu vidéo pc', 'clé cd', 'code activation'
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

def check_dealabs():
    """Scrape Dealabs - version améliorée"""
    deals = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
        }
        
        # On teste plusieurs catégories populaires
        categories = [
            'https://www.dealabs.com/groupe/high-tech',
            'https://www.dealabs.com/groupe/informatique',
            'https://www.dealabs.com/groupe/maison-jardin',
        ]
        
        for category_url in categories:
            try:
                response = requests.get(category_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher les deals (structure simplifiée)
                    deal_items = soup.find_all('article', class_=lambda x: x and 'thread' in x.lower())
                    
                    for item in deal_items[:10]:  # Limite à 10 deals par catégorie
                        try:
                            # Extraire les informations
                            title_elem = item.find('a', class_=lambda x: x and 'thread-title' in x.lower())
                            if not title_elem:
                                title_elem = item.find('strong')
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                url = title_elem.get('href', '')
                                if url and not url.startswith('http'):
                                    url = 'https://www.dealabs.com' + url
                                
                                # Extraire le prix
                                price_elem = item.find('span', class_=lambda x: x and 'thread-price' in x.lower())
                                price = price_elem.get_text(strip=True) if price_elem else "Prix non disponible"
                                
                                # Extraire la réduction
                                discount = extract_discount(item.get_text())
                                
                                # Vérifier le marchand
                                merchant_elem = item.find('span', class_=lambda x: x and 'merchant' in x.lower())
                                merchant = merchant_elem.get_text(strip=True) if merchant_elem else ""
                                
                                # Filtrer
                                if discount >= 50 and not is_excluded(title, "", merchant):
                                    deals.append({
                                        'title': title[:200],  # Limiter la longueur
                                        'price': price,
                                        'old_price': '',
                                        'discount': discount,
                                        'url': url,
                                        'source': 'Dealabs',
                                        'merchant': merchant
                                    })
                        except Exception as e:
                            continue
                
                time.sleep(2)  # Pause entre les requêtes
                
            except Exception as e:
                print(f"Erreur catégorie {category_url}: {e}")
                continue
        
    except Exception as e:
        print(f"Erreur générale Dealabs: {e}")
    
    return deals

def check_pepper_deals():
    """Alternative: Pepper.com (version internationale de Dealabs)"""
    deals = []
    
    try:
        url = "https://www.pepper.com/hot"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Structure similaire à Dealabs
            deal_items = soup.find_all('article')[:20]
            
            for item in deal_items:
                try:
                    title_elem = item.find('strong')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        discount = extract_discount(item.get_text())
                        
                        if discount >= 50:
                            link = item.find('a')
                            url = link['href'] if link else ""
                            
                            if not is_excluded(title):
                                deals.append({
                                    'title': title[:200],
                                    'price': 'Voir site',
                                    'old_price': '',
                                    'discount': discount,
                                    'url': url,
                                    'source': 'Pepper',
                                    'merchant': ''
                                })
                except:
                    continue
    
    except Exception as e:
        print(f"Erreur Pepper: {e}")
    
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
    send_telegram_message(
        "✅ <b>Bot Chasseur de Deals ACTIVÉ !</b>\n\n"
        "🔍 Surveillance active sur:\n"
        "  • Dealabs\n"
        "  • Pepper\n\n"
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
            
            # Vérifier Dealabs
            print("📡 Scraping Dealabs...")
            dealabs_deals = check_dealabs()
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
            
            # Nettoyage mémoire (garde max 1000 deals)
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
