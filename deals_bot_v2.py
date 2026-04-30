import os
import time
import requests
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from html import unescape

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = 600  # 10 minutes (plus fréquent car RSS est léger)

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
    'sweat', 'hoodie', 'jogging', 'legging', 'combinaison', 'kimono',
    'sandales', 'bottes', 'mocassin', 'espadrilles'
]

AMAZON_KEYWORDS = ['amazon.fr', 'amazon.com', 'amzn', 'amazon']

DIGITAL_KEYWORDS = [
    'dématérialisé', 'digital', 'téléchargement', 'download',
    'code psn', 'code steam', 'carte cadeau', 'gift card',
    'ebook', 'e-book', 'kindle', 'abonnement', 'streaming',
    'jeu vidéo pc', 'clé cd', 'code activation', 'carte prépayée',
    'ps plus', 'xbox live', 'nintendo online'
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
    # Chercher -XX%
    matches = re.findall(r'-\s*(\d+)\s*%', text)
    if matches:
        discounts = [int(m) for m in matches]
        return max(discounts)
    
    # Chercher XX% de réduction
    matches = re.findall(r'(\d+)\s*%\s*de\s+r[ée]duction', text.lower())
    if matches:
        discounts = [int(m) for m in matches]
        return max(discounts)
    
    return 0

def extract_price(text):
    """Extrait le prix"""
    # Chercher XX.XX€ ou XX,XX€ ou XX€
    matches = re.findall(r'(\d+(?:[,.]\d{1,2})?)\s*€', text)
    if matches:
        return matches[0].replace(',', '.') + '€'
    return None

def is_excluded(title, description=""):
    """Vérifie si le deal doit être exclu"""
    text = (title + " " + description).lower()
    
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

def parse_dealabs_rss():
    """Parse le flux RSS de Dealabs"""
    deals = []
    
    try:
        # Flux RSS Dealabs - derniers deals
        rss_url = "https://www.dealabs.com/rss/all"
        
        print(f"   📡 Récupération RSS: {rss_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(rss_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            return deals
        
        # Parser le XML
        root = ET.fromstring(response.content)
        
        # Compter les items
        items = root.findall('.//item')
        print(f"   📊 {len(items)} deals dans le flux RSS")
        
        for item in items:
            try:
                # Extraire les données
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                
                if not title_elem or not link_elem:
                    continue
                
                title = unescape(title_elem.text or "")
                link = link_elem.text or ""
                description = unescape(description_elem.text or "") if description_elem is not None else ""
                
                # Nettoyer le titre et la description
                full_text = title + " " + description
                
                # Extraire réduction
                discount = extract_discount(full_text)
                
                # Filtrer par réduction minimale
                if discount < 50:
                    continue
                
                # Vérifier exclusions
                if is_excluded(title, description):
                    continue
                
                # Extraire prix
                price = extract_price(full_text)
                if not price:
                    price = "Voir le deal"
                
                # Extraire le marchand (souvent dans la description)
                merchant = ""
                common_merchants = [
                    'Amazon', 'Cdiscount', 'Fnac', 'Darty', 'Boulanger', 
                    'Leclerc', 'Carrefour', 'Auchan', 'Lidl', 'Action',
                    'Decathlon', 'Leroy Merlin', 'Ikea', 'Cultura'
                ]
                
                for m in common_merchants:
                    if m.lower() in full_text.lower():
                        merchant = m
                        break
                
                deals.append({
                    'title': title[:200],
                    'price': price,
                    'discount': discount,
                    'url': link,
                    'source': 'Dealabs',
                    'merchant': merchant,
                    'description': description[:300]
                })
                
            except Exception as e:
                print(f"   ⚠️  Erreur parsing item: {e}")
                continue
        
    except Exception as e:
        print(f"   ❌ Erreur RSS Dealabs: {e}")
    
    return deals

def parse_pepper_rss():
    """Parse le flux RSS de Pepper"""
    deals = []
    
    try:
        rss_url = "https://www.pepper.com/rss/all"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(rss_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return deals
        
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        print(f"   📊 {len(items)} deals dans le flux RSS Pepper")
        
        for item in items:
            try:
                title_elem = item.find('title')
                link_elem = item.find('link')
                description_elem = item.find('description')
                
                if not title_elem or not link_elem:
                    continue
                
                title = unescape(title_elem.text or "")
                link = link_elem.text or ""
                description = unescape(description_elem.text or "") if description_elem is not None else ""
                
                full_text = title + " " + description
                discount = extract_discount(full_text)
                
                if discount < 50:
                    continue
                
                if is_excluded(title, description):
                    continue
                
                price = extract_price(full_text) or "Voir le deal"
                
                deals.append({
                    'title': title[:200],
                    'price': price,
                    'discount': discount,
                    'url': link,
                    'source': 'Pepper',
                    'merchant': '',
                    'description': description[:300]
                })
                
            except:
                continue
        
    except Exception as e:
        print(f"   ❌ Erreur RSS Pepper: {e}")
    
    return deals

def format_deal_message(deal):
    """Formate un deal pour Telegram"""
    merchant_info = f"\n🏪 {deal['merchant']}" if deal.get('merchant') else ""
    
    message = f"""
🔥 <b>DEAL -{deal['discount']}%</b> 🔥

📦 {deal['title']}

💰 <b>{deal['price']}</b>{merchant_info}

🌐 {deal['source']}
🔗 <a href="{deal['url']}">👉 VOIR L'OFFRE</a>

⏰ {datetime.now().strftime('%H:%M')}
"""
    return message.strip()

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🤖 BOT DEALS TELEGRAM v4 - RSS FIABLE")
    print("=" * 60)
    print(f"⏱️  Intervalle: {CHECK_INTERVAL//60} minutes")
    print(f"💰 Réduction min: -50%")
    print(f"🚫 Exclusions: Mode, Amazon, Digital")
    print(f"📡 Source: Flux RSS (100% fiable)")
    print("=" * 60)
    
    # Message de démarrage
    send_telegram_message(
        "✅ <b>Bot Deals v4 ACTIVÉ !</b>\n\n"
        "🆕 Nouvelle version avec flux RSS\n"
        "📡 Source fiable et temps réel\n\n"
        "💰 Seuil: -50% minimum\n"
        "🚫 Exclusions: Mode • Amazon • Digital\n\n"
        "⏰ Vérification toutes les 10 minutes"
    )
    
    seen_deals = set()
    check_count = 0
    
    while True:
        try:
            check_count += 1
            print(f"\n{'='*60}")
            print(f"🔍 CHECK #{check_count} - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"{'='*60}")
            
            all_deals = []
            
            # Parser RSS Dealabs
            print("📡 Parsing RSS Dealabs...")
            dealabs_deals = parse_dealabs_rss()
            all_deals.extend(dealabs_deals)
            print(f"   ✅ {len(dealabs_deals)} deals -50%+ trouvés")
            
            time.sleep(2)
            
            # Parser RSS Pepper
            print("📡 Parsing RSS Pepper...")
            pepper_deals = parse_pepper_rss()
            all_deals.extend(pepper_deals)
            print(f"   ✅ {len(pepper_deals)} deals -50%+ trouvés")
            
            # Filtrer les nouveaux
            new_deals = []
            for deal in all_deals:
                deal_id = deal['url']
                if deal_id not in seen_deals:
                    new_deals.append(deal)
                    seen_deals.add(deal_id)
            
            print(f"\n📊 Total: {len(all_deals)} deals | Nouveaux: {len(new_deals)}")
            
            # Envoyer
            if new_deals:
                print(f"\n📤 Envoi de {len(new_deals)} nouveaux deals...")
                
                # Limiter à 10 deals max par check pour éviter le spam
                deals_to_send = new_deals[:10]
                
                for i, deal in enumerate(deals_to_send, 1):
                    message = format_deal_message(deal)
                    result = send_telegram_message(message)
                    
                    if result and result.get('ok'):
                        print(f"   ✅ [{i}/{len(deals_to_send)}] {deal['title'][:40]}... -{deal['discount']}%")
                    else:
                        print(f"   ❌ [{i}/{len(deals_to_send)}] Erreur")
                    
                    time.sleep(1.5)
                
                if len(new_deals) > 10:
                    print(f"   ⚠️  {len(new_deals) - 10} deals supplémentaires non envoyés (limite spam)")
            else:
                print("😴 Aucun nouveau deal")
            
            # Nettoyage
            if len(seen_deals) > 500:
                # Garder seulement les 300 plus récents
                seen_deals_list = list(seen_deals)
                seen_deals = set(seen_deals_list[-300:])
                print("🧹 Cache nettoyé (500 → 300)")
            
            print(f"\n⏳ Prochaine vérification dans {CHECK_INTERVAL//60} minutes...")
            print(f"{'='*60}\n")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⛔ Arrêt du bot")
            send_telegram_message("⛔ Bot Deals arrêté")
            break
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            print("⏳ Nouvelle tentative dans 60s...")
            time.sleep(60)

if __name__ == "__main__":
    main()
