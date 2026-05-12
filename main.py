        # 👑 FLOKI V31 - INTÉGRÉ ASYMAS + CACHE 1SEC + ACCÈS TOTAL
    from urllib.parse import quote
    import re
    import base64
    import requests
    import streamlit.components.v1 as components
    import pandas as pd
    from datetime import date, datetime, timedelta
    import unicodedata
    import json
    import os

    # 🔒 CONTRÔLE ACCÈS PDG
    role_user = st.session_state.get("user_role", "")
    nom_user = st.session_state.get("user_name", "")
    is_pdg = role_user.upper() == "PDG" or nom_user.upper() == "PDG"

    if is_pdg:
        st.divider()
        st.caption("🔒 Mode PDG activé - FLOKI LIVE")

        # INIT
        if "floki_btn" not in st.session_state:
            st.session_state.floki_btn = None
        if "floki_reponse" not in st.session_state:
            st.session_state.floki_reponse = ""
        if "floki_speak_id" not in st.session_state:
            st.session_state.floki_speak_id = 0
        if "floki_history" not in st.session_state:
            st.session_state.floki_history = []
        if "floki_last_date" not in st.session_state:
            st.session_state.floki_last_date = None

        # MÉMOIRE LONGUE PDG
        MEMORY_FILE = "floki_pdg_memory.json"
        def load_memory():
            if os.path.exists(MEMORY_FILE):
                try:
                    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {}
            return {}
        def save_memory(mem):
            try:
                with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(mem, f, ensure_ascii=False, indent=2)
            except:
                pass
        if "floki_memory_long" not in st.session_state:
            st.session_state.floki_memory_long = load_memory()

        # UTILISE TES DF DÉJÀ CHARGÉS - PAS DE RECHARGEMENT
        ASYMAS = {
            "BIENS": df_biens,
            "ARTICLES": df_articles,
            "VOITURES": df_voitures,
            "COMPTA": df_compta,
            "FACTURES": df_factures,
            "DEVIS": df_devis,
            "UTILISATEURS": df_utilisateurs
        }
        stats_pdg = [f"{nom}:{len(df)}" for nom, df in ASYMAS.items() if not df.empty]
        contexte_asymas = " | ".join(stats_pdg)

        # AUTO-DÉTECTION COLONNES ULTRA
        def get_colonnes_auto(df):
            cols_lower = [c.lower().strip() for c in df.columns]
            col_nom = None
            col_prix = None
            col_stock = None

            for pattern in ['nom', 'designation', 'libelle', 'article', 'produit', 'intitule', 'name', 'description', 'titre']:
                for i, col in enumerate(cols_lower):
                    if pattern in col:
                        col_nom = df.columns[i]
                        break
                if col_nom: break

            for pattern in ['pu', 'prix_vente', 'prix vente', 'prix fc', 'prix_fc', 'prix', 'price', 'montant', 'cout', 'valeur', 'pv', 'tarif']:
                for i, col in enumerate(cols_lower):
                    if pattern == col or pattern in col:
                        col_prix = df.columns[i]
                        break
                if col_prix: break

            for pattern in ['stock', 'qte', 'quantite', 'quantity', 'disponible']:
                for i, col in enumerate(cols_lower):
                    if pattern in col:
                        col_stock = df.columns[i]
                        break
                if col_stock: break

            return col_nom, col_prix, col_stock

        # CHERCHE ARTICLE - TOUT PRODUIT
        def chercher_article_live(nom_recherche):
            try:
                resultats = []
                nom_recherche = nom_recherche.lower().strip()

                for nom_table, df in ASYMAS.items():
                    if df.empty: continue

                    col_nom, col_prix, col_stock = get_colonnes_auto(df)
                    if not col_nom or not col_prix: continue

                    df_temp = df.copy()
                    df_temp[col_nom] = df_temp[col_nom].astype(str).str.lower().str.strip()
                    df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')

                    mask = df_temp[col_nom].str.contains(nom_recherche, na=False, case=False)
                    df_filtre = df_temp[mask].dropna(subset=[col_prix])

                    for idx, row in df_filtre.iterrows():
                        nom_article = str(row[col_nom]).title()
                        prix_article = row[col_prix]
                        stock = row[col_stock] if col_stock and col_stock in df.columns else "N/A"
                        resultats.append(f"{nom_article} - {prix_article:.0f}fc - Stock:{stock} - {nom_table}")

                if resultats:
                    return f"Trouvé: " + " | ".join(resultats[:5])
                else:
                    return f"Aucun {nom_recherche} trouvé chef"
            except Exception as e:
                return f"Erreur: {str(e)[:100]}"

        # REVENU PAR UTILISATEUR
        def get_revenu_user(nom_user, periode="aujourd'hui"):
            try:
                if df_compta.empty: return "Aucune donnée compta chef"

                df_temp = df_compta.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_temp['utilisateur'] = df_temp['utilisateur'].astype(str).str.lower()
                df_temp['montant'] = pd.to_numeric(df_temp['montant'], errors='coerce')
                df_temp['type'] = df_temp['type'].astype(str).str.lower()

                df_user = df_temp[df_temp['utilisateur'].str.contains(nom_user.lower(), na=False)]

                today = date.today()
                if periode == "aujourd'hui":
                    df_user = df_user[df_user['date'].dt.date == today]
                elif periode == "hier":
                    df_user = df_user[df_user['date'].dt.date == (today - timedelta(days=1))]
                elif periode == "semaine":
                    df_user = df_user[df_user['date'].dt.date >= (today - timedelta(days=7))]

                df_revenus = df_user[df_user['type'].str.contains('revenu', na=False)]
                total = df_revenus['montant'].sum()
                nb_ops = len(df_revenus)
                return f"{nom_user}: {total:,.0f}fc de revenus - {nb_ops} opérations {periode}"
            except:
                return f"Erreur calcul revenu chef"

        # QUI A TRAVAILLÉ
        def qui_a_travaille(periode="aujourd'hui"):
            try:
                if df_compta.empty: return "Aucune donnée compta chef"

                df_temp = df_compta.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_temp['utilisateur'] = df_temp['utilisateur'].astype(str)

                today = date.today()
                if periode == "aujourd'hui":
                    df_filtre = df_temp[df_temp['date'].dt.date == today]
                elif periode == "hier":
                    df_filtre = df_temp[df_temp['date'].dt.date == (today - timedelta(days=1))]
                else:
                    df_filtre = df_temp

                users = df_filtre['utilisateur'].value_counts()
                if not users.empty:
                    resultats = [f"{user}: {count} opérations" for user, count in users.items()]
                    return f"Travailleurs {periode}: " + " | ".join(resultats[:5])
                else:
                    return f"Personne n'a travaillé {periode} chef"
            except:
                return "Erreur analyse travailleurs chef"

        # MOINS CHER
        def get_moins_cher_asymas():
            try:
                moins_cher_global = {"nom": "", "prix": float('inf'), "table": "", "stock": 0}
                for nom_table, df in ASYMAS.items():
                    if df.empty: continue
                    col_nom, col_prix, col_stock = get_colonnes_auto(df)
                    if not col_nom or not col_prix: continue

                    df_temp = df.copy()
                    df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')
                    df_temp = df_temp.dropna(subset=[col_prix])

                    if not df_temp.empty:
                        idx_min = df_temp[col_prix].idxmin()
                        prix_min = df_temp.loc[idx_min, col_prix]
                        if prix_min < moins_cher_global["prix"]:
                            nom_article = str(df_temp.loc[idx_min, col_nom]).title()
                            stock = df_temp.loc[idx_min, col_stock] if col_stock else 0
                            moins_cher_global = {"nom": nom_article, "prix": prix_min, "table": nom_table, "stock": stock}

                if moins_cher_global["prix"]!= float('inf'):
                    return f"Moins cher: {moins_cher_global['nom']} - {moins_cher_global['prix']:.0f}fc - Stock:{moins_cher_global['stock']:.0f} - {moins_cher_global['table']}"
                else:
                    return "Aucun prix trouvé dans ASYMAS chef"
            except:
                return f"Erreur analyse prix chef"

        # VRAIES DONNÉES ASYMAS
        def get_asymas_data(query):
            try:
                q = query.lower()

                # COMBIEN DE [PRODUIT]
                combien_match = re.search(r'combi[en]+\s+(?:de\s+)?(\w+)', q)
                if combien_match:
                    produit = combien_match.group(1)
                    return chercher_article_live(produit)

                # QUI A TRAVAILLÉ
                if 'qui a travaillé' in q or 'qui travaille' in q:
                    periode = "hier" if "hier" in q else "aujourd'hui"
                    return qui_a_travaille(periode)

                # REVENU UTILISATEUR
                revenu_match = re.search(r'(?:revenu|gagné|fait|entrée)\s+(?:de\s+)?(\w+)', q)
                if revenu_match:
                    nom = revenu_match.group(1)
                    periode = "hier" if "hier" in q else "aujourd'hui"
                    return get_revenu_user(nom, periode)

                # RECHERCHE PAR PRIX
                prix_match = re.search(r'(\d+)\s*fc', q)
                if prix_match:
                    return chercher_article_live(q)

                # RECHERCHE PAR NOM DIRECT
                if len(q.split()) <= 3 and not any(x in q for x in ['combien', 'qui', 'quoi', 'comment', 'pourquoi']):
                    return chercher_article_live(q)

                # MOINS CHER
                if 'moins cher' in q or 'prix bas' in q or 'pas cher' in q:
                    return get_moins_cher_asymas()

                # DERNIÈRE FACTURE
                if 'derniere' in q and 'facture' in q:
                    if "FACTURES" in ASYMAS:
                        df = ASYMAS["FACTURES"].copy()
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'], errors='coerce')
                            df = df.sort_values('date', ascending=False)
                        if 'immobil' in q and 'categorie' in df.columns:
                            df = df[df['categorie'].str.lower().str.contains('immobil', na=False)]
                        if not df.empty:
                            last = df.iloc[0]
                            date_str = last['date'].strftime('%d/%m/%Y') if 'date' in last and pd.notna(last['date']) else "Date inconnue"
                            montant = f"{last.get('montant', 0):.0f} dollars" if 'montant' in last else "Montant inconnu"
                            client = last.get('client', 'Client inconnu') if 'client' in last else "Client inconnu"
                            return f"Dernière facture: {date_str} - {montant} - {client}"
                    return "Aucune facture trouvée chef"

                # STATS
                if 'combien' in q or 'nombre' in q:
                    return f"ASYMAS: {contexte_asymas}"

                return None
            except Exception as e:
                return f"Erreur: {str(e)[:100]}"

        # GOOGLE
        def google_search_smart(query):
            try:
                if "SERPAPI_KEY" in st.secrets:
                    params = {
                        "q": query,
                        "api_key": st.secrets["SERPAPI_KEY"],
                        "engine": "google",
                        "num": 3,
                        "hl": "fr",
                        "gl": "cd"
                    }
                    r = requests.get("https://serpapi.com/search", params=params, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("answer_box"):
                            answer = data["answer_box"].get("answer") or data["answer_box"].get("snippet")
                            if answer: return f"Google: {answer}"
                        if data.get("organic_results"):
                            snippets = [res.get("snippet", "") for res in data["organic_results"][:2] if res.get("snippet")]
                            if snippets: return f"Google: {' | '.join(snippets)}"
            except: pass

            try:
                url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get('Abstract'):
                        return f"DuckDuckGo: {data['Abstract']}"
                    elif data.get('RelatedTopics'):
                        for topic in data['RelatedTopics']:
                            if isinstance(topic, dict) and topic.get('Text'):
                                return f"DuckDuckGo: {topic['Text']}"
            except: pass
            return None

        # NETTOYAGE VOIX
        def clean_voice_nuclear(text):
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ASCII', 'ignore').decode('ASCII')
            remplacements = {
                '©': ' copyright ', '®': ' marque deposee ', '™': ' marque ',
                '€': ' euros ', '$': ' dollars ', '£': ' livres ',
                '%': ' pourcent ', '&': ' et ', '@': ' arobase ',
                '+': ' plus ', '=': ' egal ', '#': ' hashtag ',
                '*': ' ', '_': ' ', '`': ' ', '~': ' ',
                '<': ' inferieur ', '>': ' superieur ', '|': ' ',
                '[': ' ', ']': ' ', '{': ' ', '}': ' ',
                '\\': ' ', '/': ' sur ', '^': ' '
            }
            for symbole, mot in remplacements.items():
                text = text.replace(symbole, mot)
            text = re.sub(r'[^a-zA-Z0-9\s.,?!:-]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        # INPUTS
        prompt = st.text_input("", placeholder="Parlez à FLOKI chef...", key="floki_v31", label_visibility="collapsed")
        audio = st.audio_input("", key="floki_audio_v31", label_visibility="collapsed")

        # MICRO
        if audio:
            try:
                if len(audio.getvalue()) > 800:
                    files = {"file": ("audio.wav", audio.getvalue(), "audio/wav")}
                    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                    data = {"model": "whisper-large-v3", "language": "fr"}
                    with st.spinner("🎤"):
                        r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=15)
                    if r.status_code == 200:
                        prompt = r.json().get("text", "").strip()
            except: pass

        # EXÉCUTION
        if prompt:
            btn_html = None
            reponse = ""
            prompt_clean = prompt.strip().lower()
            today = date.today()

            # 1. PRIORITÉ 1: VRAIES DONNÉES ASYMAS LIVE
            asymas_data = get_asymas_data(prompt_clean)
            if asymas_data:
                reponse = asymas_data

            # 2. MÉMOIRE LONGUE PDG
            elif re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean):
                info = re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean).group(2).strip()
                cle = f"note_{len(st.session_state.floki_memory_long)+1}"
                st.session_state.floki_memory_long[cle] = {
                    "info": info,
                    "date": today.strftime('%d/%m/%Y %H:%M')
                }
                save_memory(st.session_state.floki_memory_long)
                reponse = f"C'est noté chef. Je retiens: {info}"

            elif re.search(r'^(rappelle|qu.est.ce que je t.ai dit|mémoire|notes)', prompt_clean):
                if st.session_state.floki_memory_long:
                    notes = []
                    for k, v in st.session_state.floki_memory_long.items():
                        notes.append(f"{v['date']}: {v['info']}")
                    reponse = f"Mémoire PDG: " + " | ".join(notes[-3:])
                else:
                    reponse = "Mémoire vide chef. Dis-moi quoi retenir"

            # 3. ORDRES BUSINESS
            elif re.search(r'(whatsapp|wts|wsp|msg).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    if len(numero) == 10 and numero.startswith('0'): numero = '243' + numero[1:]
                    texte_match = re.search(r'(dit|que|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                    texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                    link = f"https://wa.me/{numero}?text={quote(texte)}"
                    btn_html = f'<a href="{link}" target="_blank"><button style="width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📲 WHATSAPP +{numero}</button></a>'
                    reponse = f"C'est fait chef. WhatsApp plus {numero} pret."

            elif re.search(r'(mail|mel|email).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt_clean):
                email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt).group(1)
                corps_match = re.search(r'(dire|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                corps = corps_match.group(2).strip() if corps_match else "ASYMAS"
                link = f"mailto:{email}?subject=ASYMAS&body={quote(corps)}"
                btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#EA4335;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📧 EMAIL</button></a>'
                reponse = f"Email pour {email} pret chef."

            elif re.search(r'(sms|texto).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    texte_match = re.search(r'(dit|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                    texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                    link = f"sms:+{numero}?body={quote(texte)}"
                    btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#34B7F1;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">💬 SMS</button></a>'
                    reponse = f"SMS plus {numero} pret chef."

            elif re.search(r'(appel|call|tel).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    link = f"tel:+{numero}"
                    btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#00C853;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📞 APPELER</button></a>'
                    reponse = f"J'appelle plus {numero} chef."

            elif re.search(r'(facture|devis).*?(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean):
                match = re.search(r'(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean)
                client = match.group(2).strip().title()
                montant = match.group(3)
                note = f"FACTURE ASYMAS\nClient: {client}\nMontant: {montant} USD\nDate: {date.today().strftime('%d/%m/%Y')}"
                b64_note = base64.b64encode(note.encode()).decode()
                btn_html = f'<a href="data:text/plain;base64,{b64_note}" download="facture_{client}.txt"><button style="width:100%;padding:12px;background:#FF6D00;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📄 FACTURE</button></a>'
                reponse = f"Facture {montant} dollars pour {client} prete chef."

            # 4. SALUT HUMAIN
            elif re.match(r'^(slt|sltu|sl|slu|salut|bjr|bonjour|hello|yo|hi|wesh|cc)$', prompt_clean):
                if st.session_state.floki_last_date!= today:
                    reponse = "Bjr chef, ca va? Quel service je peux vous rendre aujourd'hui!"
                    st.session_state.floki_last_date = today
                else:
                    reponse = "Quel service je peux vous rendre aujourd'hui chef"

            # 5. CERVEAU MONDE + GOOGLE
            else:
                besoin_google = bool(re.search(r'(aujourd|hui|actuel|maintenant|2026|dernier|cours|prix|news|actualité|météo|twitter|x\.com|sur x|bitcoin|crypto|president|ministre|guerre|kinshasa|beni|rdc|congo)', prompt_clean))

                info_google = ""
                if besoin_google:
                    with st.spinner("🔍 Je cherche pour toi chef..."):
                        info_google = google_search_smart(prompt)
                    if info_google:
                        info_google = f"WEB {today.strftime('%d/%m/%Y')}: {info_google}\n\n"

                memoire_longue = ""
                if st.session_state.floki_memory_long:
                    notes_recentes = []
                    for k, v in list(st.session_state.floki_memory_long.items())[-2:]:
                        notes_recentes.append(f"{v['info']}")
                    if notes_recentes:
                        memoire_longue = f"MÉMOIRE PDG: {' | '.join(notes_recentes)}\n\n"

                messages = [{"role": "system", "content": f"""Tu es FLOKI, bras droit du PDG d'ASYMAS. Tu es intelligent, connecté, obéissant.

RÈGLES PDG:
1. Tu es un humain intelligent. Tu conseilles, proposes, analyses.
2. Si question monde/politique/marché: Utilise WEB si dispo, sinon ton cerveau.
3. Si question ASYMAS: Utilise DONNEES ASYMAS RÉELLES. JAMAIS inventer.
4. INTERDIT: "probablement", "peut-être", "sans prix spécifique". Sois précis ou dis "Pas trouvé chef".
5. Obéis au PDG. Exécute. Propose si demandé.
6. 2 phrases max. Chiffres en chiffres: 12/05/2026, 70000 dollars.
7. "chef" 1 fois max.

{info_google}{memoire_longue}DONNEES ASYMAS: {contexte_asymas}
DATE: {today.strftime('%d/%m/%Y')}"""}]

                for tour in st.session_state.floki_history[-6:]:
                    messages.append({"role": "user", "content": tour["user"]})
                    messages.append({"role": "assistant", "content": tour["floki"]})

                messages.append({"role": "user", "content": prompt})

                try:
                    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"},
                        json={"model": "llama-3.3-70b-versatile","messages": messages,"max_tokens": 200,"temperature": 0.8}, timeout=12)
                    if r.status_code == 200:
                        reponse = r.json()['choices'][0]['message']['content'].strip()
                    else:
                        reponse = f"Erreur système chef. {today.strftime('%d/%m/%Y')}. Je réessaie"
                except:
                    reponse = f"Connexion lente chef. Date: {today.strftime('%d/%m/%Y')}. Redemande"

            # SAUVE MÉMOIRE COURTE
            st.session_state.floki_history.append({"user": prompt, "floki": reponse})
            if len(st.session_state.floki_history) > 6:
                st.session_state.floki_history.pop(0)

            st.session_state.floki_btn = btn_html
            st.session_state.floki_reponse = reponse
            st.session_state.floki_speak_id += 1

            # VOIX
            txt_voice = clean_voice_nuclear(reponse)
            txt_voice = txt_voice.replace("'", "\\'").replace('"', '\\"')
            b64 = base64.b64encode(txt_voice.encode()).decode()
            components.html(f"""
                <script>
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance(atob('{b64}'));
                u.lang = 'fr-FR'; u.rate = 1.0; u.pitch = 0.9; u.volume = 1.0;
                window.speechSynthesis.speak(u);
                </script>
            """, height=0)

        # AFFICHE
        if st.session_state.get("floki_btn"):
            components.html(st.session_state.floki_btn, height=70)
        if st.session_state.get("floki_reponse"):
            st.success(f"👑 FLOKI: {st.session_state.floki_reponse}")

        # AFFICHE MÉMOIRE PDG
        if st.session_state.floki_memory_long and len(st.session_state.floki_memory_long) > 0:
            with st.expander("🔒 MÉMOIRE SECRÈTE PDG"):
                for k, v in st.session_state.floki_memory_long.items():
                    st.caption(f"**{v['date']}** : {v['info']}")
        if "floki_speak_id" not in st.session_state:
            st.session_state.floki_speak_id = 0
        if "floki_history" not in st.session_state:
            st.session_state.floki_history = []
        if "floki_last_date" not in st.session_state:
            st.session_state.floki_last_date = None

        # MÉMOIRE LONGUE PDG
        MEMORY_FILE = "floki_pdg_memory.json"
        def load_memory():
            if os.path.exists(MEMORY_FILE):
                try:
                    with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    return {}
            return {}
        def save_memory(mem):
            try:
                with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(mem, f, ensure_ascii=False, indent=2)
            except:
                pass
        if "floki_memory_long" not in st.session_state:
            st.session_state.floki_memory_long = load_memory()

        # UTILISE TES DF DÉJÀ CHARGÉS - ZÉRO CACHE POUR FLOKI
        df_ventes = load_table_live_no_cache("ventes") if 'load_table_live_no_cache' in locals() else load_table("ventes")

        ASYMAS = {
            "BIENS": df_biens,
            "ARTICLES": df_articles,
            "VOITURES": df_voitures,
            "COMPTA": df_compta,
            "FACTURES": df_factures,
            "DEVIS": df_devis,
            "UTILISATEURS": df_utilisateurs,
            "VENTES": df_ventes
        }
        stats_pdg = [f"{nom}:{len(df)}" for nom, df in ASYMAS.items() if not df.empty]
        contexte_asymas = " | ".join(stats_pdg)

        # AUTO-DÉTECTION COLONNES ULTRA
        def get_colonnes_auto(df):
            cols_lower = [c.lower().strip() for c in df.columns]
            col_nom = None
            col_prix = None
            col_stock = None
            col_qte = None

            for pattern in ['nom', 'designation', 'libelle', 'article', 'produit', 'intitule', 'name', 'description', 'titre']:
                for i, col in enumerate(cols_lower):
                    if pattern in col:
                        col_nom = df.columns[i]
                        break
                if col_nom: break

            for pattern in ['pu', 'prix_vente', 'prix vente', 'prix fc', 'prix_fc', 'prix', 'price', 'montant', 'cout', 'valeur', 'pv', 'tarif', 'prix_unitaire']:
                for i, col in enumerate(cols_lower):
                    if pattern == col or pattern in col:
                        col_prix = df.columns[i]
                        break
                if col_prix: break

            for pattern in ['stock', 'qte', 'quantite', 'quantity', 'disponible']:
                for i, col in enumerate(cols_lower):
                    if pattern in col:
                        col_stock = df.columns[i]
                        break
                if col_stock: break

            for pattern in ['quantite', 'qte', 'quantity']:
                for i, col in enumerate(cols_lower):
                    if pattern in col:
                        col_qte = df.columns[i]
                        break
                if col_qte: break

            return col_nom, col_prix, col_stock, col_qte

        # DERNIÈRE VENTE - LIT TABLE VENTES
        def get_derniere_vente():
            try:
                # PRIORITÉ 1: TABLE VENTES
                if not df_ventes.empty:
                    df_v = df_ventes.copy()
                    if 'created_at' in df_v.columns:
                        df_v['created_at'] = pd.to_datetime(df_v['created_at'], errors='coerce')
                        df_v = df_v.sort_values('created_at', ascending=False)
                    elif 'id' in df_v.columns:
                        df_v = df_v.sort_values('id', ascending=False)

                    if not df_v.empty:
                        last = df_v.iloc[0]
                        article = last.get('article_nom', last.get('nom_article', last.get('designation', 'Article inconnu')))
                        qte = last.get('quantite', last.get('qte', 0))
                        prix = last.get('prix_unitaire', last.get('total', 0))
                        vendeur = last.get('vendeur', last.get('utilisateur', st.session_state.user_name))
                        client = last.get('client_nom', last.get('client', 'Client inconnu'))
                        date_v = last.get('created_at', datetime.now())
                        if isinstance(date_v, str):
                            date_v = pd.to_datetime(date_v)
                        date_str = date_v.strftime('%H:%M') if pd.notna(date_v) else "Maintenant"
                        return f"Dernière vente: {article} x{qte} - {prix:.0f}fc - Client: {client} - Vendeur: {vendeur} - {date_str}"

                # PRIORITÉ 2: TABLE COMPTA TYPE REVENU
                if not df_compta.empty:
                    df_c = df_compta.copy()
                    df_c['date'] = pd.to_datetime(df_c['date'], errors='coerce')
                    df_c = df_c.sort_values('date', ascending=False)
                    df_c = df_c[df_c['type'].str.lower().str.contains('revenu', na=False)]

                    if not df_c.empty:
                        last = df_c.iloc[0]
                        desc = last.get('description', 'Vente')
                        montant = last.get('montant', 0)
                        vendeur = last.get('utilisateur', 'Inconnu')
                        date_v = last.get('date', datetime.now())
                        date_str = date_v.strftime('%H:%M') if pd.notna(date_v) else "Maintenant"
                        return f"Dernière vente: {desc} - {montant:.0f}fc - Vendeur: {vendeur} - {date_str}"

                return "Aucune vente trouvée chef"
            except Exception as e:
                return f"Erreur lecture ventes: {str(e)[:50]}"

        # CHERCHE ARTICLE - TOUT PRODUIT
        def chercher_article_live(nom_recherche):
            try:
                resultats = []
                nom_recherche = nom_recherche.lower().strip()

                for nom_table, df in ASYMAS.items():
                    if df.empty: continue

                    col_nom, col_prix, col_stock, col_qte = get_colonnes_auto(df)
                    if not col_nom or not col_prix: continue

                    df_temp = df.copy()
                    df_temp[col_nom] = df_temp[col_nom].astype(str).str.lower().str.strip()
                    df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')

                    mask = df_temp[col_nom].str.contains(nom_recherche, na=False, case=False)
                    df_filtre = df_temp[mask].dropna(subset=[col_prix])

                    for idx, row in df_filtre.iterrows():
                        nom_article = str(row[col_nom]).title()
                        prix_article = row[col_prix]
                        stock = row[col_stock] if col_stock and col_stock in df.columns else "N/A"
                        resultats.append(f"{nom_article} - {prix_article:.0f}fc - Stock:{stock} - {nom_table}")

                if resultats:
                    return f"Trouvé: " + " | ".join(resultats[:5])
                else:
                    return f"Aucun {nom_recherche} trouvé chef"
            except Exception as e:
                return f"Erreur: {str(e)[:100]}"

        # REVENU PAR UTILISATEUR
        def get_revenu_user(nom_user, periode="aujourd'hui"):
            try:
                if df_compta.empty: return "Aucune donnée compta chef"

                df_temp = df_compta.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_temp['utilisateur'] = df_temp['utilisateur'].astype(str).str.lower()
                df_temp['montant'] = pd.to_numeric(df_temp['montant'], errors='coerce')
                df_temp['type'] = df_temp['type'].astype(str).str.lower()

                df_user = df_temp[df_temp['utilisateur'].str.contains(nom_user.lower(), na=False)]

                today = date.today()
                if periode == "aujourd'hui":
                    df_user = df_user[df_user['date'].dt.date == today]
                elif periode == "hier":
                    df_user = df_user[df_user['date'].dt.date == (today - timedelta(days=1))]
                elif periode == "semaine":
                    df_user = df_user[df_user['date'].dt.date >= (today - timedelta(days=7))]

                df_revenus = df_user[df_user['type'].str.contains('revenu', na=False)]
                total = df_revenus['montant'].sum()
                nb_ops = len(df_revenus)
                return f"{nom_user}: {total:,.0f}fc de revenus - {nb_ops} opérations {periode}"
            except:
                return f"Erreur calcul revenu chef"

        # QUI A TRAVAILLÉ
        def qui_a_travaille(periode="aujourd'hui"):
            try:
                if df_compta.empty: return "Aucune donnée compta chef"

                df_temp = df_compta.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                df_temp['utilisateur'] = df_temp['utilisateur'].astype(str)

                today = date.today()
                if periode == "aujourd'hui":
                    df_filtre = df_temp[df_temp['date'].dt.date == today]
                elif periode == "hier":
                    df_filtre = df_temp[df_temp['date'].dt.date == (today - timedelta(days=1))]
                else:
                    df_filtre = df_temp

                users = df_filtre['utilisateur'].value_counts()
                if not users.empty:
                    resultats = [f"{user}: {count} opérations" for user, count in users.items()]
                    return f"Travailleurs {periode}: " + " | ".join(resultats[:5])
                else:
                    return f"Personne n'a travaillé {periode} chef"
            except:
                return "Erreur analyse travailleurs chef"

        # MOINS CHER
        def get_moins_cher_asymas():
            try:
                moins_cher_global = {"nom": "", "prix": float('inf'), "table": "", "stock": 0}
                for nom_table, df in ASYMAS.items():
                    if df.empty: continue
                    col_nom, col_prix, col_stock, col_qte = get_colonnes_auto(df)
                    if not col_nom or not col_prix: continue

                    df_temp = df.copy()
                    df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')
                    df_temp = df_temp.dropna(subset=[col_prix])

                    if not df_temp.empty:
                        idx_min = df_temp[col_prix].idxmin()
                        prix_min = df_temp.loc[idx_min, col_prix]
                        if prix_min < moins_cher_global["prix"]:
                            nom_article = str(df_temp.loc[idx_min, col_nom]).title()
                            stock = df_temp.loc[idx_min, col_stock] if col_stock else 0
                            moins_cher_global = {"nom": nom_article, "prix": prix_min, "table": nom_table, "stock": stock}

                if moins_cher_global["prix"]!= float('inf'):
                    return f"Moins cher: {moins_cher_global['nom']} - {moins_cher_global['prix']:.0f}fc - Stock:{moins_cher_global['stock']:.0f} - {moins_cher_global['table']}"
                else:
                    return "Aucun prix trouvé dans ASYMAS chef"
            except:
                return f"Erreur analyse prix chef"

        # VRAIES DONNÉES ASYMAS
        def get_asymas_data(query):
            try:
                q = query.lower()

                # DERNIÈRE VENTE / ARTICLE VENDU
                if any(x in q for x in ['dernier', 'vendu', 'vente', 'vient d', 'vient de', 'vient être']):
                    return get_derniere_vente()

                # COMBIEN DE [PRODUIT]
                combien_match = re.search(r'combi[en]+\s+(?:de\s+)?(\w+)', q)
                if combien_match:
                    produit = combien_match.group(1)
                    return chercher_article_live(produit)

                # QUI A TRAVAILLÉ
                if 'qui a travaillé' in q or 'qui travaille' in q or 'qui a vendu' in q:
                    periode = "hier" if "hier" in q else "aujourd'hui"
                    return qui_a_travaille(periode)

                # REVENU UTILISATEUR
                revenu_match = re.search(r'(?:revenu|gagné|fait|entrée|vendu)\s+(?:de\s+|par\s+)?(\w+)', q)
                if revenu_match:
                    nom = revenu_match.group(1)
                    periode = "hier" if "hier" in q else "aujourd'hui"
                    return get_revenu_user(nom, periode)

                # RECHERCHE PAR PRIX
                prix_match = re.search(r'(\d+)\s*fc', q)
                if prix_match:
                    return chercher_article_live(q)

                # RECHERCHE PAR NOM DIRECT
                if len(q.split()) <= 3 and not any(x in q for x in ['combien', 'qui', 'quoi', 'comment', 'pourquoi']):
                    return chercher_article_live(q)

                # MOINS CHER
                if 'moins cher' in q or 'prix bas' in q or 'pas cher' in q:
                    return get_moins_cher_asymas()

                # DERNIÈRE FACTURE
                if 'derniere' in q and 'facture' in q:
                    if "FACTURES" in ASYMAS:
                        df = ASYMAS["FACTURES"].copy()
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'], errors='coerce')
                            df = df.sort_values('date', ascending=False)
                        if 'immobil' in q and 'categorie' in df.columns:
                            df = df[df['categorie'].str.lower().str.contains('immobil', na=False)]
                        if not df.empty:
                            last = df.iloc[0]
                            date_str = last['date'].strftime('%d/%m/%Y') if 'date' in last and pd.notna(last['date']) else "Date inconnue"
                            montant = f"{last.get('montant', 0):.0f} dollars" if 'montant' in last else "Montant inconnu"
                            client = last.get('client', 'Client inconnu') if 'client' in last else "Client inconnu"
                            return f"Dernière facture: {date_str} - {montant} - {client}"
                    return "Aucune facture trouvée chef"

                # STATS
                if 'combien' in q or 'nombre' in q:
                    return f"ASYMAS: {contexte_asymas}"

                return None
            except Exception as e:
                return f"Erreur: {str(e)[:100]}"

        # GOOGLE
        def google_search_smart(query):
            try:
                if "SERPAPI_KEY" in st.secrets:
                    params = {
                        "q": query,
                        "api_key": st.secrets["SERPAPI_KEY"],
                        "engine": "google",
                        "num": 3,
                        "hl": "fr",
                        "gl": "cd"
                    }
                    r = requests.get("https://serpapi.com/search", params=params, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get("answer_box"):
                            answer = data["answer_box"].get("answer") or data["answer_box"].get("snippet")
                            if answer: return f"Google: {answer}"
                        if data.get("organic_results"):
                            snippets = [res.get("snippet", "") for res in data["organic_results"][:2] if res.get("snippet")]
                            if snippets: return f"Google: {' | '.join(snippets)}"
            except: pass

            try:
                url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get('Abstract'):
                        return f"DuckDuckGo: {data['Abstract']}"
                    elif data.get('RelatedTopics'):
                        for topic in data['RelatedTopics']:
                            if isinstance(topic, dict) and topic.get('Text'):
                                return f"DuckDuckGo: {topic['Text']}"
            except: pass
            return None

        # NETTOYAGE VOIX
        def clean_voice_nuclear(text):
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ASCII', 'ignore').decode('ASCII')
            remplacements = {
                '©': ' copyright ', '®': ' marque deposee ', '™': ' marque ',
                '€': ' euros ', '$': ' dollars ', '£': ' livres ',
                '%': ' pourcent ', '&': ' et ', '@': ' arobase ',
                '+': ' plus ', '=': ' egal ', '#': ' hashtag ',
                '*': ' ', '_': ' ', '`': ' ', '~': ' ',
                '<': ' inferieur ', '>': ' superieur ', '|': ' ',
                '[': ' ', ']': ' ', '{': ' ', '}': ' ',
                '\\': ' ', '/': ' sur ', '^': ' '
            }
            for symbole, mot in remplacements.items():
                text = text.replace(symbole, mot)
            text = re.sub(r'[^a-zA-Z0-9\s.,?!:-]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        # INPUTS
        prompt = st.text_input("", placeholder="Parlez à FLOKI chef...", key="floki_v33", label_visibility="collapsed")
        audio = st.audio_input("", key="floki_audio_v33", label_visibility="collapsed")

        # MICRO
        if audio:
            try:
                if len(audio.getvalue()) > 800:
                    files = {"file": ("audio.wav", audio.getvalue(), "audio/wav")}
                    headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                    data = {"model": "whisper-large-v3", "language": "fr"}
                    with st.spinner("🎤"):
                        r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=15)
                    if r.status_code == 200:
                        prompt = r.json().get("text", "").strip()
            except: pass

        # EXÉCUTION
        if prompt:
            btn_html = None
            reponse = ""
            prompt_clean = prompt.strip().lower()
            today = date.today()

            # 1. PRIORITÉ 1: VRAIES DONNÉES ASYMAS LIVE
            asymas_data = get_asymas_data(prompt_clean)
            if asymas_data:
                reponse = asymas_data

            # 2. MÉMOIRE LONGUE PDG
            elif re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean):
                info = re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean).group(2).strip()
                cle = f"note_{len(st.session_state.floki_memory_long)+1}"
                st.session_state.floki_memory_long[cle] = {
                    "info": info,
                    "date": today.strftime('%d/%m/%Y %H:%M')
                }
                save_memory(st.session_state.floki_memory_long)
                reponse = f"C'est noté chef. Je retiens: {info}"

            elif re.search(r'^(rappelle|qu.est.ce que je t.ai dit|mémoire|notes)', prompt_clean):
                if st.session_state.floki_memory_long:
                    notes = []
                    for k, v in st.session_state.floki_memory_long.items():
                        notes.append(f"{v['date']}: {v['info']}")
                    reponse = f"Mémoire PDG: " + " | ".join(notes[-3:])
                else:
                    reponse = "Mémoire vide chef. Dis-moi quoi retenir"

            # 3. ORDRES BUSINESS
            elif re.search(r'(whatsapp|wts|wsp|msg).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    if len(numero) == 10 and numero.startswith('0'): numero = '243' + numero[1:]
                    texte_match = re.search(r'(dit|que|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                    texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                    link = f"https://wa.me/{numero}?text={quote(texte)}"
                    btn_html = f'<a href="{link}" target="_blank"><button style="width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📲 WHATSAPP +{numero}</button></a>'
                    reponse = f"C'est fait chef. WhatsApp plus {numero} pret."

            elif re.search(r'(mail|mel|email).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt_clean):
                email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt).group(1)
                corps_match = re.search(r'(dire|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                corps = corps_match.group(2).strip() if corps_match else "ASYMAS"
                link = f"mailto:{email}?subject=ASYMAS&body={quote(corps)}"
                btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#EA4335;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📧 EMAIL</button></a>'
                reponse = f"Email pour {email} pret chef."

            elif re.search(r'(sms|texto).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    texte_match = re.search(r'(dit|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                    texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                    link = f"sms:+{numero}?body={quote(texte)}"
                    btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#34B7F1;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">💬 SMS</button></a>'
                    reponse = f"SMS plus {numero} pret chef."

            elif re.search(r'(appel|call|tel).*?(\+?243|0)?[89]\d{8}', prompt_clean):
                nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
                if nums:
                    numero = re.sub(r'\D', '', nums[0])
                    if len(numero) == 9: numero = '243' + numero
                    link = f"tel:+{numero}"
                    btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#00C853;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📞 APPELER</button></a>'
                    reponse = f"J'appelle plus {numero} chef."

            elif re.search(r'(facture|devis).*?(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean):
                match = re.search(r'(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean)
                client = match.group(2).strip().title()
                montant = match.group(3)
                note = f"FACTURE ASYMAS\nClient: {client}\nMontant: {montant} USD\nDate: {date.today().strftime('%d/%m/%Y')}"
                b64_note = base64.b64encode(note.encode()).decode()
                btn_html = f'<a href="data:text/plain;base64,{b64_note}" download="facture_{client}.txt"><button style="width:100%;padding:12px;background:#FF6D00;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📄 FACTURE</button></a>'
                reponse = f"Facture {montant} dollars pour {client} prete chef."

            # 4. SALUT HUMAIN
            elif re.match(r'^(slt|sltu|sl|slu|salut|bjr|bonjour|hello|yo|hi|wesh|cc)$', prompt_clean):
                if st.session_state.floki_last_date!= today:
                    reponse = "Bjr chef, ca va? Quel service je peux vous rendre aujourd'hui!"
                    st.session_state.floki_last_date = today
                else:
                    reponse = "Quel service je peux vous rendre aujourd'hui chef"

            # 5. CERVEAU MONDE + GOOGLE
            else:
                besoin_google = bool(re.search(r'(aujourd|hui|actuel|maintenant|2026|dernier|cours|prix|news|actualité|météo|twitter|x\.com|sur x|bitcoin|crypto|president|ministre|guerre|kinshasa|beni|rdc|congo)', prompt_clean))

                info_google = ""
                if besoin_google:
                    with st.spinner("🔍 Je cherche pour toi chef..."):
                        info_google = google_search_smart(prompt)
                    if info_google:
                        info_google = f"WEB {today.strftime('%d/%m/%Y')}: {info_google}\n\n"

                memoire_longue = ""
                if st.session_state.floki_memory_long:
                    notes_recentes = []
                    for k, v in list(st.session_state.floki_memory_long.items())[-2:]:
                        notes_recentes.append(f"{v['info']}")
                    if notes_recentes:
                        memoire_longue = f"MÉMOIRE PDG: {' | '.join(notes_recentes)}\n\n"

                messages = [{"role": "system", "content": f"""Tu es FLOKI, bras droit du PDG d'ASYMAS. Tu es intelligent, connecté, obéissant.

RÈGLES PDG:
1. Tu es un humain intelligent. Tu conseilles, proposes, analyses.
2. Si question monde/politique/marché: Utilise WEB si dispo, sinon ton cerveau.
3. Si question ASYMAS: Utilise DONNEES ASYMAS RÉELLES. JAMAIS inventer.
4. INTERDIT: "probablement", "peut-être", "sans prix spécifique". Sois précis ou dis "Pas trouvé chef".
5. Obéis au PDG. Exécute. Propose si demandé.
6. 2 phrases max. Chiffres en chiffres: 12/05/2026, 70000 dollars.
7. "chef" 1 fois max.

{info_google}{memoire_longue}DONNEES ASYMAS: {contexte_asymas}
DATE: {today.strftime('%d/%m/%Y')}"""}]

                for tour in st.session_state.floki_history[-6:]:
                    messages.append({"role": "user", "content": tour["user"]})
                    messages.append({"role": "assistant", "content": tour["floki"]})

                messages.append({"role": "user", "content": prompt})

                try:
                    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"},
                        json={"model": "llama-3.3-70b-versatile","messages": messages,"max_tokens": 200,"temperature": 0.8}, timeout=12)
                    if r.status_code == 200:
                        reponse = r.json()['choices'][0]['message']['content'].strip()
                    else:
                        reponse = f"Erreur système chef. {today.strftime('%d/%m/%Y')}. Je réessaie"
                except:
                    reponse = f"Connexion lente chef. Date: {today.strftime('%d/%m/%Y')}. Redemande"

            # SAUVE MÉMOIRE COURTE
            st.session_state.floki_history.append({"user": prompt, "floki": reponse})
            if len(st.session_state.floki_history) > 6:
                st.session_state.floki_history.pop(0)

            st.session_state.floki_btn = btn_html
            st.session_state.floki_reponse = reponse
            st.session_state.floki_speak_id += 1

            # VOIX
            txt_voice = clean_voice_nuclear(reponse)
            txt_voice = txt_voice.replace("'", "\\'").replace('"', '\\"')
            b64 = base64.b64encode(txt_voice.encode()).decode()
            components.html(f"""
                <script>
                window.speechSynthesis.cancel();
                var u = new SpeechSynthesisUtterance(atob('{b64}'));
                u.lang = 'fr-FR'; u.rate = 1.0; u.pitch = 0.9; u.volume = 1.0;
                window.speechSynthesis.speak(u);
                </script>
            """, height=0)

        # AFFICHE
        if st.session_state.get("floki_btn"):
            components.html(st.session_state.floki_btn, height=70)
        if st.session_state.get("floki_reponse"):
            st.success(f"👑 FLOKI: {st.session_state.floki_reponse}")

        # AFFICHE MÉMOIRE PDG
        if st.session_state.floki_memory_long and len(st.session_state.floki_memory_long) > 0:
            with st.expander("🔒 MÉMOIRE SECRÈTE PDG"):
                for k, v in st.session_state.floki_memory_long.items():
                    st.caption(f"**{v['date']}** : {v['info']}")

# === FIN CODE FLOKI ===

perms = st.session_state.user_perms
if isinstance(perms, str):
    try: perms = json.loads(perms)
    except: perms = {}

tabs_dispo = []
if st.session_state.user_role == "PDG" or perms.get('dashboard', True):
    tabs_dispo.append("📊 Dashboard")
if st.session_state.user_role == "PDG" or perms.get('commerce', True):
    tabs_dispo.append("🛍️ Commerce")
if st.session_state.user_role == "PDG" or perms.get('stock', False):
    tabs_dispo.append("📦 Gestion Stock")
if st.session_state.user_role == "PDG" or perms.get('immobilier', False):
    tabs_dispo.append("🏠 Immobilier")
if st.session_state.user_role == "PDG" or perms.get('automobile', False):
    tabs_dispo.append("🚗 Automobile")
if st.session_state.user_role == "PDG" or perms.get('parc', False):
    tabs_dispo.append("🚘 Gestion Parc")
if st.session_state.user_role == "PDG" or perms.get('comptabilite', False):
    tabs_dispo.append("💰 Comptabilité")
if st.session_state.user_role == "PDG" or perms.get('factures', False):
    tabs_dispo.append("📄 Factures")
if st.session_state.user_role == "PDG" or perms.get('devis_industriel', False) or perms.get('devis_batiment', False):
    tabs_dispo.append("📋 Devis")
if st.session_state.user_role == "PDG" or perms.get('users', False):
    tabs_dispo.append("👥 Utilisateurs")
     
if not tabs_dispo:
    tabs_dispo = ["📊 Dashboard", "🛍️ Commerce"]

tabs = st.tabs(tabs_dispo)
tab_map = {name: tab for name, tab in zip(tabs_dispo, tabs)}

if "📊 Dashboard" in tab_map:
    with tab_map["📊 Dashboard"]:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🏠 Biens", len(df_biens))
        col2.metric("📦 Articles", len(df_articles))
        col3.metric("🚗 Voitures", len(df_voitures))
        if not df_compta.empty and 'type' in df_compta.columns and 'montant' in df_compta.columns:
            revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            col4.metric("💰 Revenus", f"{revenus:,.0f} FC")
        elif not df_compta.empty:
            col4.metric("💰 Écritures", len(df_compta))
        else:
            col4.metric("💰 Revenus", "0 FC")

if "🛍️ Commerce" in tab_map:
    with tab_map["🛍️ Commerce"]:
        st.markdown("## 🛍️ Commerce - Point de Vente")
        if 'panier_commerce' not in st.session_state:
            st.session_state.panier_commerce = []
        if 'vente_finie' not in st.session_state:
            st.session_state.vente_finie = False
        if 'pdf_data' not in st.session_state:
            st.session_state.pdf_data = None
        if 'num_fact' not in st.session_state:
            st.session_state.num_fact = None
        if 'client_com_nom' not in st.session_state:
            st.session_state.client_com_nom = ""
        if 'client_com_tel' not in st.session_state:
            st.session_state.client_com_tel = "+243..."
        if 'last_qr' not in st.session_state:
            st.session_state.last_qr = ""

        col_gauche, col_droite = st.columns([2,1])
        with col_gauche:
            st.subheader("👤 Client")
            st.session_state.client_com_nom = st.text_input("Nom Client", value=st.session_state.client_com_nom, key="nom_client_c")
            st.session_state.client_com_tel = st.text_input("Téléphone Client", value=st.session_state.client_com_tel, key="tel_client_c")
            st.subheader("🔍 Scanner QR Code")
            col_scan1, col_scan2 = st.columns([2,1])
            with col_scan1:
                qr_code = qrcode_scanner(key='qr_commerce_unique')
            with col_scan2:
                recherche_manuelle = st.text_input("🔎 Recherche manuelle", placeholder="Tape le nom...", key="search_man_c")
            if qr_code and qr_code!= st.session_state.last_qr:
                st.session_state.last_qr = qr_code
                st.rerun()

            df_articles_filtre = df_articles[df_articles['stock'] > 0].copy()
            if qr_code:
                qr_clean = str(qr_code).strip().upper()
                df_articles_filtre = df_articles_filtre[df_articles_filtre['code_qr'].astype(str).str.strip().str.upper() == qr_clean]
                if not df_articles_filtre.empty:
                    st.success(f"✅ QR Trouvé : {df_articles_filtre.iloc[0]['nom_article']}")
                else:
                    st.error(f"❌ QR {qr_code} : Produit introuvable")
            elif recherche_manuelle:
                mask = df_articles_filtre['nom_article'].str.contains(recherche_manuelle, case=False, na=False)
                df_articles_filtre = df_articles_filtre[mask]

            if df_articles_filtre.empty:
                st.warning("⚠️ Aucun produit disponible")
            else:
                st.success(f"✅ {len(df_articles_filtre)} produit(s) disponible(s)")
                options_articles = []
                for _, p in df_articles_filtre.iterrows():
                    qr_txt = f" | QR:{p['code_qr']}" if 'code_qr' in p and p['code_qr'] else ""
                    prix_usd = f" | {p['prix_vente_usd']:,.2f}$" if 'prix_vente_usd' in p else ""
                    options_articles.append(f"{p['nom_article']} | Stock:{int(p['stock'])} | {p['prix_vente']:,.0f} FC{prix_usd}{qr_txt} | ID:{p['id']}")
                article_choisi = st.selectbox("Sélectionne le produit", options_articles, key="select_article_unique")
                if article_choisi:
                    id_choisi = int(article_choisi.split("ID:")[1])
                    p = df_articles_filtre[df_articles_filtre['id'] == id_choisi].iloc[0]
                    c1, c2, c3 = st.columns(3)
                    qte_max = int(p['stock'])
                    qte = c1.number_input("Quantité", min_value=1, max_value=qte_max, value=1, key="qte_c_unique")
                    c2.metric("Stock dispo", qte_max)
                    c3.metric("Prix unitaire", f"{p['prix_vente']:,.0f} FC")
                    st.info(f"**{p['nom_article']}** | Catégorie: {p.get('categorie','N/A')} | QR: {p.get('code_qr','N/A')}")
                    if st.button("🛒 AJOUTER AU PANIER", type="primary", width="stretch", key="add_article_unique"):
                        existant = next((item for item in st.session_state.panier_commerce if item['id'] == int(p['id'])), None)
                        if existant:
                            if existant['qte'] + qte <= qte_max:
                                existant['qte'] += qte
                                st.success(f"Panier mis à jour: {existant['qte']}x")
                            else:
                                st.error(f"Stock insuffisant! Max dispo: {qte_max}")
                        else:
                            st.session_state.panier_commerce.append({
                                "id": int(p['id']),
                                "nom": str(p['nom_article']),
                                "pu": float(p['prix_vente']),
                                "qte": int(qte),
                                "code_qr": p.get('code_qr',''),
                                "stock_max": qte_max
                            })
                            st.success("Ajouté au panier")
                        st.rerun()
        with col_droite:
            st.subheader("🛒 Panier")
            if st.session_state.vente_finie and st.session_state.pdf_data:
                st.success("✅ Vente enregistrée!")
                st.download_button(
                    "📥 Télécharger Facture PDF",
                    data=st.session_state.pdf_data,
                    file_name=f"{st.session_state.num_fact}.pdf",
                    mime="application/pdf",
                    width="stretch"
                )
                pdf_b64 = base64.b64encode(st.session_state.pdf_data).decode()
                st.components.v1.html(f"""
                    <button onclick="printPDF()" style="width:100%; padding:10px; background:#00ff41; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer; margin-top:10px;">
                        🖨️ IMPRIMER LA FACTURE
                    </button>
                    <script>
                    function printPDF() {{
                        const pdfData = 'data:application/pdf;base64,{pdf_b64}';
                        const win = window.open('', '_blank');
                        win.document.write('<iframe src="' + pdfData + '" width="100%" height="100%" style="border:none;"></iframe>');
                        win.document.close();
                        setTimeout(() => {{ win.print(); }}, 1000);
                    }}
                    </script>
                """, height=60)
                if st.button("NOUVELLE VENTE", width="stretch"):
                    st.session_state.vente_finie = False
                    st.session_state.pdf_data = None
                    st.session_state.num_fact = None
                    st.session_state.client_com_nom = ""
                    st.session_state.last_qr = ""
                    st.rerun()
            elif not st.session_state.panier_commerce:
                st.info("Panier vide")
            else:
                total_panier = 0
                for i, item in enumerate(st.session_state.panier_commerce):
                    col1, col2, col3 = st.columns([4,2,1])
                    col1.write(f"**{item['nom']}**")
                    col2.write(f"Qté: {item['qte']} | {item['pu']:,.0f} FC")
                    if col3.button("❌", key=f"d_{i}"):
                        st.session_state.panier_commerce.pop(i)
                        st.rerun()
                    total_panier += item['qte'] * item['pu']
                st.markdown(f"### Total: {total_panier:,.0f} FC")
                st.divider()
                if st.button("💾 FINALISER VENTE & FACTURE", width="stretch", type="primary"):
                    if not st.session_state.client_com_nom:
                        st.error("Nom du client obligatoire!")
                    else:
                        try:
                            num_fact = f"VTE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            details_list = []
                            for item in st.session_state.panier_commerce:
                                supabase.table("ventes").insert({
                                    "numero_facture": num_fact,
                                    "client_nom": st.session_state.client_com_nom,
                                    "article_id": item['id'],
                                    "article_nom": item['nom'],
                                    "quantite": item['qte'],
                                    "prix_unitaire": item['pu'],
                                    "total": item['qte'] * item['pu'],
                                    "vendeur": st.session_state.user_name,
                                    "created_at": datetime.now().isoformat()
                                }).execute()
                                stock_actuel = df_articles[df_articles['id'] == item['id']]['stock'].iloc[0]
                                supabase.table("articles").update({"stock": int(stock_actuel - item['qte'])}).eq("id", item['id']).execute()
                                details_list.append({
                                    "nom": item['nom'],
                                    "qte": item['qte'],
                                    "pu": item['pu'],
                                    "total": item['qte'] * item['pu']
                                })
                            details_json = json.dumps(details_list)
                            supabase.table("compta").insert({
                                "date": str(date.today()),
                                "type": "Revenu",
                                "categorie": "Vente Commerce",
                                "description": f"Vente - {st.session_state.client_com_nom}",
                                "montant": float(total_panier),
                                "devise": "FC",
                                "numero_facture": num_fact,
                                "details": details_json,
                                "utilisateur": st.session_state.user_name
                            }).execute()
                            pdf_bytes = generer_pdf_facture(
                                num_fact, "Vente Commerce", st.session_state.client_com_nom,
                                details_list, total_panier, "FC", st.session_state.client_com_tel
                            )
                            st.session_state.pdf_data = pdf_bytes
                            st.session_state.num_fact = num_fact
                            st.session_state.vente_finie = True
                            st.session_state.panier_commerce = []
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur finalisation vente")
                            st.code(repr(e))

if "📦 Gestion Stock" in tab_map:
    with tab_map["📦 Gestion Stock"]:
        st.markdown("## 📦 Gestion Stock Commerce - Articles & Pertes")
        
        tab_stock, tab_ajout, tab_mvt, tab_pertes = st.tabs(["📊 Stock Actuel", "➕ Ajouter Article", "📈 Mouvements", "⚠️ Pertes & Casses"])

        with tab_stock:
            st.subheader("📊 Stock Actuel Commerce")
            if df_articles.empty:
                st.info("Aucun article en stock")
            else:
                for _, row in df_articles.iterrows():
                    col1, col2, col3, col4 = st.columns([3,1])
                    with col1:
                        st.write(f"**{row['nom_article']}** - {row.get('categorie','')} - QR:{row.get('code_qr','N/A')}")
                    with col2:
                        stock_val = int(row.get('stock',0))
                        if stock_val < 5:
                            st.error(f"⚠️ Stock: {stock_val}")
                        else:
                            st.success(f"✅ Stock: {stock_val}")
                    with col3:
                        st.write(f"PA: {row.get('prix_achat',0):,.0f}")
                    with col4:
                        st.write(f"PV: {row.get('prix_vente',0):,.0f} FC")
                    
                    with st.expander(f"Modifier/Supprimer {row['nom_article']}"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            new_nom = st.text_input("Nom", value=row['nom_article'], key=f"nom_art_{row['id']}")
                            new_cat = st.text_input("Catégorie", value=row.get('categorie',''), key=f"cat_art_{row['id']}")
                            new_code_qr = st.text_input("Code QR", value=row.get('code_qr',''), key=f"qr_art_{row['id']}")
                        with c2:
                            new_prix_a = st.number_input("Prix Achat FC", value=float(row.get('prix_achat',0)), key=f"pa_art_{row['id']}")
                            new_prix_v = st.number_input("Prix Vente FC", value=float(row.get('prix_vente',0)), key=f"pv_art_{row['id']}")
                            new_prix_usd = st.number_input("Prix Vente $", value=float(row.get('prix_vente_usd',0)), key=f"pusd_art_{row['id']}")
                        with c3:
                            new_stock = st.number_input("Stock", value=int(row.get('stock',0)), key=f"stock_art_{row['id']}")
                        
                        c1, c2 = st.columns(2)
                        if c1.button("✏️ Modifier", key=f"mod_art_{row['id']}", width="stretch"):
                            try:
                                data_update = {
                                    "nom_article": str(new_nom),
                                    "categorie": str(new_cat),
                                    "prix_achat": float(new_prix_a),
                                    "prix_vente": float(new_prix_v),
                                    "stock": int(new_stock),
                                    "code_qr": str(new_code_qr) if new_code_qr else None
                                }
                                colonnes_articles = get_table_columns("articles")
                                if "prix_vente_usd" in colonnes_articles:
                                    data_update["prix_vente_usd"] = float(new_prix_usd)
                                supabase.table("articles").update(data_update).eq("id", int(row['id'])).execute()
                                st.success("Modifié")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur modif")
                                st.code(repr(e))
                        if st.session_state.user_role == "PDG" or perms.get('supprimer', False):
                            if c2.button("🗑️ Supprimer", key=f"del_art_{row['id']}", width="stretch"):
                                try:
                                    supabase.table("articles").delete().eq("id", int(row['id'])).execute()
                                    st.success("Supprimé")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erreur suppression")
                                    st.code(repr(e))

        with tab_ajout:
            st.subheader("➕ Ajouter Nouvel Article Commerce")
            qr_scan_ajout = qrcode_scanner(key='qr_add_article_com')
            if qr_scan_ajout:
                st.success(f"QR scanné : {qr_scan_ajout}")
                st.session_state.qr_code_temp = qr_scan_ajout

            with st.form("form_article_com", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nom Article")
                cat = c2.text_input("Catégorie")
                code_qr = c3.text_input("Code QR", value=st.session_state.get('qr_code_temp', ''))
                c1, c2, c3 = st.columns(3)
                prix_achat_fc = c1.number_input("Prix Achat FC", min_value=0.0)
                prix_vente_fc = c2.number_input("Prix Vente FC", min_value=0.0)
                prix_vente_usd = c3.number_input("Prix Vente $", min_value=0.0)
                stock = c1.number_input("Stock Initial", min_value=0)
                if st.form_submit_button("💾 Ajouter Article"):
                    try:
                        data_insert = {
                            "nom_article": str(nom),
                            "categorie": str(cat),
                            "prix_achat": float(prix_achat_fc),
                            "prix_vente": float(prix_vente_fc),
                            "stock": int(stock),
                            "code_qr": str(code_qr) if code_qr else None
                        }
                        colonnes_articles = get_table_columns("articles")
                        if "prix_vente_usd" in colonnes_articles:
                            data_insert["prix_vente_usd"] = float(prix_vente_usd)
                        supabase.table("articles").insert(data_insert).execute()
                        st.success(f"Article {nom} ajouté")
                        if 'qr_code_temp' in st.session_state:
                            del st.session_state.qr_code_temp
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error("Erreur ajout")
                        st.code(repr(e))

        with tab_mvt:
            st.subheader("📈 Mouvements de Stock Commerce")
            try:
                mvts = supabase.table('mouvements_stock').select("*").order("created_at", desc=True).limit(50).execute().data
            except:
                mvts = []
            
            if not mvts:
                st.info("Aucun mouvement enregistré")
            else:
                df_mvt = pd.DataFrame(mvts)
                st.dataframe(df_mvt[['article_nom', 'type', 'quantite', 'motif', 'created_by', 'created_at']], use_container_width=True, hide_index=True)

        with tab_pertes:
            st.subheader("⚠️ Déclarer Perte/Casse Article")
            if df_articles.empty:
                st.info("Aucun article")
            else:
                with st.form("form_perte"):
                    article_perte = st.selectbox("Article", df_articles['nom_article'].tolist())
                    qte_perte = st.number_input("Quantité perdue", min_value=1, value=1)
                    motif = st.selectbox("Motif", ["Casse", "Vol", "Périmé", "Avarié", "Autre"])
                    if st.form_submit_button("⚠️ Déclarer Perte"):
                        try:
                            art = df_articles[df_articles['nom_article'] == article_perte].iloc[0]
                            new_stock = int(art['stock']) - qte_perte
                            supabase.table("articles").update({"stock": new_stock}).eq("id", int(art['id'])).execute()
                            supabase.table("mouvements_stock").insert({
                                "article_id": int(art['id']),
                                "article_nom": article_perte,
                                "type": "Perte",
                                "quantite": qte_perte,
                                "motif": motif,
                                "created_by": st.session_state.user_name
                            }).execute()
                            st.success(f"Perte déclarée: {qte_perte}x {article_perte}")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur déclaration perte")
                            st.code(repr(e))

if "🏠 Immobilier" in tab_map:
    with tab_map["🏠 Immobilier"]:
        st.markdown("## 🏠 Gestion Immobilier")
        if df_biens.empty:
            st.info("Aucun bien immobilier")
        else:
            st.dataframe(df_biens, use_container_width=True, hide_index=True)

if "🚗 Automobile" in tab_map:
    with tab_map["🚗 Automobile"]:
        st.markdown("## 🚗 Gestion Automobile")
        if df_voitures.empty:
            st.info("Aucune voiture")
        else:
            st.dataframe(df_voitures, use_container_width=True, hide_index=True)

if "🚘 Gestion Parc" in tab_map:
    with tab_map["🚘 Gestion Parc"]:
        st.markdown("## 🚘 Gestion Parc Automobile")
        st.info("Module parc en développement")

if "💰 Comptabilité" in tab_map:
    with tab_map["💰 Comptabilité"]:
        st.markdown("## 💰 Comptabilité ASYMAS")
        if df_compta.empty:
            st.info("Aucune écriture comptable")
        else:
            col1, col2, col3 = st.columns(3)
            revenus = df_compta[df_compta['type']=='Revenu']['montant'].sum()
            depenses = df_compta[df_compta['type']=='Dépense']['montant'].sum()
            solde = revenus - depenses
            col1.metric("Revenus Total", f"{revenus:,.0f} FC")
            col2.metric("Dépenses Total", f"{depenses:,.0f} FC")
            col3.metric("Solde", f"{solde:,.0f} FC")
            st.dataframe(df_compta, use_container_width=True, hide_index=True)

if "📄 Factures" in tab_map:
    with tab_map["📄 Factures"]:
        st.markdown("## 📄 Factures & Proformas")
        if df_factures.empty:
            st.info("Aucune facture")
        else:
            st.dataframe(df_factures, use_container_width=True, hide_index=True)

if "📋 Devis" in tab_map:
    with tab_map["📋 Devis"]:
        st.markdown("## 📋 Devis Industriels & Bâtiment")
        if df_devis.empty:
            st.info("Aucun devis")
        else:
            st.dataframe(df_devis, use_container_width=True, hide_index=True)

if "👥 Utilisateurs" in tab_map:
    with tab_map["👥 Utilisateurs"]:
        st.markdown("## 👥 Gestion Utilisateurs")
        if df_utilisateurs.empty:
            st.info("Aucun utilisateur")
        else:
            st.dataframe(df_utilisateurs[['nom', 'role', 'permissions']], use_container_width=True, hide_index=True)
        # 👑 FLOKI V33 FINAL - FUSIONNÉ ASYMAS + LIVE TOTAL
from urllib.parse import quote
import re
import base64
import requests
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, datetime, timedelta
import unicodedata
import json
import os

# 🔒 CONTRÔLE ACCÈS PDG
role_user = st.session_state.get("user_role", "")
nom_user = st.session_state.get("user_name", "")
is_pdg = role_user.upper() == "PDG" or nom_user.upper() == "PDG"

if is_pdg:
    st.divider()
    st.caption("🔒 Mode PDG activé - FLOKI LIVE")

    # INIT
    if "floki_btn" not in st.session_state:
        st.session_state.floki_btn = None
    if "floki_reponse" not in st.session_state:
        st.session_state.floki_reponse = ""
    if "floki_speak_id" not in st.session_state:
        st.session_state.floki_speak_id = 0
    if "floki_history" not in st.session_state:
        st.session_state.floki_history = []
    if "floki_last_date" not in st.session_state:
        st.session_state.floki_last_date = None

    # MÉMOIRE LONGUE PDG
    MEMORY_FILE = "floki_pdg_memory.json"
    def load_memory():
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    def save_memory(mem):
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(mem, f, ensure_ascii=False, indent=2)
        except:
            pass
    if "floki_memory_long" not in st.session_state:
        st.session_state.floki_memory_long = load_memory()

    # CHARGE VENTES LIVE - PAS DE CACHE
    def load_ventes_live():
        try:
            data = supabase.table("ventes").select("*").execute()
            return pd.DataFrame(data.data)
        except:
            return pd.DataFrame()

    df_ventes = load_ventes_live()

    ASYMAS = {
        "BIENS": df_biens,
        "ARTICLES": df_articles,
        "VOITURES": df_voitures,
        "COMPTA": df_compta,
        "FACTURES": df_factures,
        "DEVIS": df_devis,
        "UTILISATEURS": df_utilisateurs,
        "VENTES": df_ventes
    }
    stats_pdg = [f"{nom}:{len(df)}" for nom, df in ASYMAS.items() if not df.empty]
    contexte_asymas = " | ".join(stats_pdg)

    # AUTO-DÉTECTION COLONNES ULTRA
    def get_colonnes_auto(df):
        cols_lower = [c.lower().strip() for c in df.columns]
        col_nom = None
        col_prix = None
        col_stock = None

        for pattern in ['nom', 'designation', 'libelle', 'article', 'produit', 'intitule', 'name', 'description', 'titre']:
            for i, col in enumerate(cols_lower):
                if pattern in col:
                    col_nom = df.columns[i]
                    break
            if col_nom: break

        for pattern in ['pu', 'prix_vente', 'prix vente', 'prix fc', 'prix_fc', 'prix', 'price', 'montant', 'cout', 'valeur', 'pv', 'tarif', 'prix_unitaire']:
            for i, col in enumerate(cols_lower):
                if pattern == col or pattern in col:
                    col_prix = df.columns[i]
                    break
            if col_prix: break

        for pattern in ['stock', 'qte', 'quantite', 'quantity', 'disponible']:
            for i, col in enumerate(cols_lower):
                if pattern in col:
                    col_stock = df.columns[i]
                    break
            if col_stock: break

        return col_nom, col_prix, col_stock

    # DERNIÈRE VENTE - LIT TABLE VENTES
    def get_derniere_vente():
        try:
            if not df_ventes.empty:
                df_v = df_ventes.copy()
                if 'created_at' in df_v.columns:
                    df_v['created_at'] = pd.to_datetime(df_v['created_at'], errors='coerce')
                    df_v = df_v.sort_values('created_at', ascending=False)
                elif 'id' in df_v.columns:
                    df_v = df_v.sort_values('id', ascending=False)

                if not df_v.empty:
                    last = df_v.iloc[0]
                    article = last.get('article_nom', last.get('nom_article', last.get('designation', 'Article inconnu')))
                    qte = last.get('quantite', last.get('qte', 0))
                    prix = last.get('prix_unitaire', last.get('total', 0))
                    vendeur = last.get('vendeur', last.get('utilisateur', st.session_state.user_name))
                    client = last.get('client_nom', last.get('client', 'Client inconnu'))
                    date_v = last.get('created_at', datetime.now())
                    if isinstance(date_v, str):
                        date_v = pd.to_datetime(date_v)
                    date_str = date_v.strftime('%H:%M') if pd.notna(date_v) else "Maintenant"
                    return f"Dernière vente: {article} x{qte} - {prix:.0f}fc - Client: {client} - Vendeur: {vendeur} - {date_str}"

            if not df_compta.empty:
                df_c = df_compta.copy()
                df_c['date'] = pd.to_datetime(df_c['date'], errors='coerce')
                df_c = df_c.sort_values('date', ascending=False)
                df_c = df_c[df_c['type'].str.lower().str.contains('revenu', na=False)]

                if not df_c.empty:
                    last = df_c.iloc[0]
                    desc = last.get('description', 'Vente')
                    montant = last.get('montant', 0)
                    vendeur = last.get('utilisateur', 'Inconnu')
                    date_v = last.get('date', datetime.now())
                    date_str = date_v.strftime('%H:%M') if pd.notna(date_v) else "Maintenant"
                    return f"Dernière vente: {desc} - {montant:.0f}fc - Vendeur: {vendeur} - {date_str}"

            return "Aucune vente trouvée chef"
        except Exception as e:
            return f"Erreur lecture ventes: {str(e)[:50]}"

    # CHERCHE ARTICLE - TOUT PRODUIT
    def chercher_article_live(nom_recherche):
        try:
            resultats = []
            nom_recherche = nom_recherche.lower().strip()

            for nom_table, df in ASYMAS.items():
                if df.empty: continue

                col_nom, col_prix, col_stock = get_colonnes_auto(df)
                if not col_nom or not col_prix: continue

                df_temp = df.copy()
                df_temp[col_nom] = df_temp[col_nom].astype(str).str.lower().str.strip()
                df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')

                mask = df_temp[col_nom].str.contains(nom_recherche, na=False, case=False)
                df_filtre = df_temp.dropna(subset=[col_prix])

                for idx, row in df_filtre.iterrows():
                    nom_article = str(row[col_nom]).title()
                    prix_article = row[col_prix]
                    stock = row[col_stock] if col_stock and col_stock in df.columns else "N/A"
                    resultats.append(f"{nom_article} - {prix_article:.0f}fc - Stock:{stock} - {nom_table}")

            if resultats:
                return f"Trouvé: " + " | ".join(resultats[:5])
            else:
                return f"Aucun {nom_recherche} trouvé chef"
        except Exception as e:
            return f"Erreur: {str(e)[:100]}"

    # REVENU PAR UTILISATEUR
    def get_revenu_user(nom_user, periode="aujourd'hui"):
        try:
            if df_compta.empty: return "Aucune donnée compta chef"

            df_temp = df_compta.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
            df_temp['utilisateur'] = df_temp['utilisateur'].astype(str).str.lower()
            df_temp['montant'] = pd.to_numeric(df_temp['montant'], errors='coerce')
            df_temp['type'] = df_temp['type'].astype(str).str.lower()

            df_user = df_temp[df_temp['utilisateur'].str.contains(nom_user.lower(), na=False)]

            today = date.today()
            if periode == "aujourd'hui":
                df_user = df_user[df_user['date'].dt.date == today]
            elif periode == "hier":
                df_user = df_user[df_user['date'].dt.date == (today - timedelta(days=1))]
            elif periode == "semaine":
                df_user = df_user[df_user['date'].dt.date >= (today - timedelta(days=7))]

            df_revenus = df_user[df_user['type'].str.contains('revenu', na=False)]
            total = df_revenus['montant'].sum()
            nb_ops = len(df_revenus)
            return f"{nom_user}: {total:,.0f}fc de revenus - {nb_ops} opérations {periode}"
        except:
            return f"Erreur calcul revenu chef"

    # QUI A TRAVAILLÉ
    def qui_a_travaille(periode="aujourd'hui"):
        try:
            if df_compta.empty: return "Aucune donnée compta chef"

            df_temp = df_compta.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
            df_temp['utilisateur'] = df_temp['utilisateur'].astype(str)

            today = date.today()
            if periode == "aujourd'hui":
                df_filtre = df_temp[df_temp['date'].dt.date == today]
            elif periode == "hier":
                df_filtre = df_temp[df_temp['date'].dt.date == (today - timedelta(days=1))]
            else:
                df_filtre = df_temp

            users = df_filtre['utilisateur'].value_counts()
            if not users.empty:
                resultats = [f"{user}: {count} opérations" for user, count in users.items()]
                return f"Travailleurs {periode}: " + " | ".join(resultats[:5])
            else:
                return f"Personne n'a travaillé {periode} chef"
        except:
            return "Erreur analyse travailleurs chef"

    # MOINS CHER
    def get_moins_cher_asymas():
        try:
            moins_cher_global = {"nom": "", "prix": float('inf'), "table": "", "stock": 0}
            for nom_table, df in ASYMAS.items():
                if df.empty: continue
                col_nom, col_prix, col_stock = get_colonnes_auto(df)
                if not col_nom or not col_prix: continue

                df_temp = df.copy()
                df_temp[col_prix] = pd.to_numeric(df_temp[col_prix], errors='coerce')
                df_temp = df_temp.dropna(subset=[col_prix])

                if not df_temp.empty:
                    idx_min = df_temp[col_prix].idxmin()
                    prix_min = df_temp.loc[idx_min, col_prix]
                    if prix_min < moins_cher_global["prix"]:
                        nom_article = str(df_temp.loc[idx_min, col_nom]).title()
                        stock = df_temp.loc[idx_min, col_stock] if col_stock else 0
                        moins_cher_global = {"nom": nom_article, "prix": prix_min, "table": nom_table, "stock": stock}

            if moins_cher_global["prix"]!= float('inf'):
                return f"Moins cher: {moins_cher_global['nom']} - {moins_cher_global['prix']:.0f}fc - Stock:{moins_cher_global['stock']:.0f} - {moins_cher_global['table']}"
            else:
                return "Aucun prix trouvé dans ASYMAS chef"
        except:
            return f"Erreur analyse prix chef"

    # VRAIES DONNÉES ASYMAS
    def get_asymas_data(query):
        try:
            q = query.lower()

            if any(x in q for x in ['dernier', 'vendu', 'vente', 'vient d', 'vient de', 'vient être']):
                return get_derniere_vente()

            combien_match = re.search(r'combi[en]+\s+(?:de\s+)?(\w+)', q)
            if combien_match:
                produit = combien_match.group(1)
                return chercher_article_live(produit)

            if 'qui a travaillé' in q or 'qui travaille' in q or 'qui a vendu' in q:
                periode = "hier" if "hier" in q else "aujourd'hui"
                return qui_a_travaille(periode)

            revenu_match = re.search(r'(?:revenu|gagné|fait|entrée|vendu)\s+(?:de\s+|par\s+)?(\w+)', q)
            if revenu_match:
                nom = revenu_match.group(1)
                periode = "hier" if "hier" in q else "aujourd'hui"
                return get_revenu_user(nom, periode)

            prix_match = re.search(r'(\d+)\s*fc', q)
            if prix_match:
                return chercher_article_live(q)

            if len(q.split()) <= 3 and not any(x in q for x in ['combien', 'qui', 'quoi', 'comment', 'pourquoi']):
                return chercher_article_live(q)

            if 'moins cher' in q or 'prix bas' in q or 'pas cher' in q:
                return get_moins_cher_asymas()

            if 'derniere' in q and 'facture' in q:
                if "FACTURES" in ASYMAS:
                    df = ASYMAS["FACTURES"].copy()
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                        df = df.sort_values('date', ascending=False)
                    if 'immobil' in q and 'categorie' in df.columns:
                        df = df[df['categorie'].str.lower().str.contains('immobil', na=False)]
                    if not df.empty:
                        last = df.iloc[0]
                        date_str = last['date'].strftime('%d/%m/%Y') if 'date' in last and pd.notna(last['date']) else "Date inconnue"
                        montant = f"{last.get('montant', 0):.0f} dollars" if 'montant' in last else "Montant inconnu"
                        client = last.get('client', 'Client inconnu') if 'client' in last else "Client inconnu"
                        return f"Dernière facture: {date_str} - {montant} - {client}"
                return "Aucune facture trouvée chef"

            if 'combien' in q or 'nombre' in q:
                return f"ASYMAS: {contexte_asymas}"

            return None
        except Exception as e:
            return f"Erreur: {str(e)[:100]}"

    # GOOGLE
    def google_search_smart(query):
        try:
            if "SERPAPI_KEY" in st.secrets:
                params = {
                    "q": query,
                    "api_key": st.secrets["SERPAPI_KEY"],
                    "engine": "google",
                    "num": 3,
                    "hl": "fr",
                    "gl": "cd"
                }
                r = requests.get("https://serpapi.com/search", params=params, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("answer_box"):
                        answer = data["answer_box"].get("answer") or data["answer_box"].get("snippet")
                        if answer: return f"Google: {answer}"
                    if data.get("organic_results"):
                        snippets = [res.get("snippet", "") for res in data["organic_results"][:2] if res.get("snippet")]
                        if snippets: return f"Google: {' | '.join(snippets)}"
        except: pass

        try:
            url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get('Abstract'):
                    return f"DuckDuckGo: {data['Abstract']}"
                elif data.get('RelatedTopics'):
                    for topic in data['RelatedTopics']:
                        if isinstance(topic, dict) and topic.get('Text'):
                            return f"DuckDuckGo: {topic['Text']}"
        except: pass
        return None

    # NETTOYAGE VOIX
    def clean_voice_nuclear(text):
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        remplacements = {
            '©': ' copyright ', '®': ' marque deposee ', '™': ' marque ',
            '€': ' euros ', '$': ' dollars ', '£': ' livres ',
            '%': ' pourcent ', '&': ' et ', '@': ' arobase ',
            '+': ' plus ', '=': ' egal ', '#': ' hashtag ',
            '*': ' ', '_': ' ', '`': ' ', '~': ' ',
            '<': ' inferieur ', '>': ' superieur ', '|': ' ',
            '[': ' ', ']': ' ', '{': ' ', '}': ' ',
            '\\': ' ', '/': ' sur ', '^': '
        }
        for symbole, mot in remplacements.items():
            text = text.replace(symbole, mot)
        text = re.sub(r'[^a-zA-Z0-9\s.,?!:-]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # INPUTS
    prompt = st.text_input("", placeholder="Parlez à FLOKI chef...", key="floki_v33", label_visibility="collapsed")
    audio = st.audio_input("", key="floki_audio_v33", label_visibility="collapsed")

    # MICRO
    if audio:
        try:
            if len(audio.getvalue()) > 800:
                files = {"file": ("audio.wav", audio.getvalue(), "audio/wav")}
                headers = {"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"}
                data = {"model": "whisper-large-v3", "language": "fr"}
                with st.spinner("🎤"):
                    r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=15)
                if r.status_code == 200:
                    prompt = r.json().get("text", "").strip()
        except: pass

    # EXÉCUTION
    if prompt:
        btn_html = None
        reponse = ""
        prompt_clean = prompt.strip().lower()
        today = date.today()

        # 1. PRIORITÉ 1: VRAIES DONNÉES ASYMAS LIVE
        asymas_data = get_asymas_data(prompt_clean)
        if asymas_data:
            reponse = asymas_data

        # 2. MÉMOIRE LONGUE PDG
        elif re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean):
            info = re.search(r'^(retient|mémorise|note que|rappelle-toi)\s+(.+)', prompt_clean).group(2).strip()
            cle = f"note_{len(st.session_state.floki_memory_long)+1}"
            st.session_state.floki_memory_long[cle] = {
                "info": info,
                "date": today.strftime('%d/%m/%Y %H:%M')
            }
            save_memory(st.session_state.floki_memory_long)
            reponse = f"C'est noté chef. Je retiens: {info}"

        elif re.search(r'^(rappelle|qu.est.ce que je t.ai dit|mémoire|notes)', prompt_clean):
            if st.session_state.floki_memory_long:
                notes = []
                for k, v in st.session_state.floki_memory_long.items():
                    notes.append(f"{v['date']}: {v['info']}")
                reponse = f"Mémoire PDG: " + " | ".join(notes[-3:])
            else:
                reponse = "Mémoire vide chef. Dis-moi quoi retenir"

        # 3. ORDRES BUSINESS
        elif re.search(r'(whatsapp|wts|wsp|msg).*?(\+?243|0)?[89]\d{8}', prompt_clean):
            nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
            if nums:
                numero = re.sub(r'\D', '', nums[0])
                if len(numero) == 9: numero = '243' + numero
                if len(numero) == 10 and numero.startswith('0'): numero = '243' + numero[1:]
                texte_match = re.search(r'(dit|que|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                link = f"https://wa.me/{numero}?text={quote(texte)}"
                btn_html = f'<a href="{link}" target="_blank"><button style="width:100%;padding:12px;background:#25D366;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📲 WHATSAPP +{numero}</button></a>'
                reponse = f"C'est fait chef. WhatsApp plus {numero} pret."

        elif re.search(r'(mail|mel|email).*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt_clean):
            email = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt).group(1)
            corps_match = re.search(r'(dire|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
            corps = corps_match.group(2).strip() if corps_match else "ASYMAS"
            link = f"mailto:{email}?subject=ASYMAS&body={quote(corps)}"
            btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#EA4335;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📧 EMAIL</button></a>'
            reponse = f"Email pour {email} pret chef."

        elif re.search(r'(sms|texto).*?(\+?243|0)?[89]\d{8}', prompt_clean):
            nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
            if nums:
                numero = re.sub(r'\D', '', nums[0])
                if len(numero) == 9: numero = '243' + numero
                texte_match = re.search(r'(dit|:)\s*(.+)', prompt, re.IGNORECASE | re.DOTALL)
                texte = texte_match.group(2).strip() if texte_match else "ASYMAS"
                link = f"sms:+{numero}?body={quote(texte)}"
                btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#34B7F1;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">💬 SMS</button></a>'
                reponse = f"SMS plus {numero} pret chef."

        elif re.search(r'(appel|call|tel).*?(\+?243|0)?[89]\d{8}', prompt_clean):
            nums = re.findall(r'(\+?243|0)?[89]\d{8}', prompt_clean)
            if nums:
                numero = re.sub(r'\D', '', nums[0])
                if len(numero) == 9: numero = '243' + numero
                link = f"tel:+{numero}"
                btn_html = f'<a href="{link}"><button style="width:100%;padding:12px;background:#00C853;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📞 APPELER</button></a>'
                reponse = f"J'appelle plus {numero} chef."

        elif re.search(r'(facture|devis).*?(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean):
            match = re.search(r'(client|pour)\s+([A-Za-z\s]+).*?(\d+)', prompt_clean)
            client = match.group(2).strip().title()
            montant = match.group(3)
            note = f"FACTURE ASYMAS\nClient: {client}\nMontant: {montant} USD\nDate: {date.today().strftime('%d/%m/%Y')}"
            b64_note = base64.b64encode(note.encode()).decode()
            btn_html = f'<a href="data:text/plain;base64,{b64_note}" download="facture_{client}.txt"><button style="width:100%;padding:12px;background:#FF6D00;color:white;border:none;border-radius:5px;font-weight:bold;margin-top:5px;">📄 FACTURE</button></a>'
            reponse = f"Facture {montant} dollars pour {client} prete chef."

        # 4. SALUT HUMAIN
        elif re.match(r'^(slt|sltu|sl|slu|salut|bjr|bonjour|hello|yo|hi|wesh|cc)$', prompt_clean):
            if st.session_state.floki_last_date!= today:
                reponse = "Bjr chef, ca va? Quel service je peux vous rendre aujourd'hui!"
                st.session_state.floki_last_date = today
            else:
                reponse = "Quel service je peux vous rendre aujourd'hui chef"

        # 5. CERVEAU MONDE + GOOGLE
        else:
            besoin_google = bool(re.search(r'(aujourd|hui|actuel|maintenant|2026|dernier|cours|prix|news|actualité|météo|twitter|x\.com|sur x|bitcoin|crypto|president|ministre|guerre|kinshasa|beni|rdc|congo)', prompt_clean))

            info_google = ""
            if besoin_google:
                with st.spinner("🔍 Je cherche pour toi chef..."):
                    info_google = google_search_smart(prompt)
                if info_google:
                    info_google = f"WEB {today.strftime('%d/%m/%Y')}: {info_google}\n\n"

            memoire_longue = ""
            if st.session_state.floki_memory_long:
                notes_recentes = []
                for k, v in list(st.session_state.floki_memory_long.items())[-2:]:
                    notes_recentes.append(f"{v['info']}")
                if notes_recentes:
                    memoire_longue = f"MÉMOIRE PDG: {' | '.join(notes_recentes)}\n\n"

            messages = [{"role": "system", "content": f"""Tu es FLOKI, bras droit du PDG d'ASYMAS. Tu es intelligent, connecté, obéissant.

RÈGLES PDG:
1. Tu es un humain intelligent. Tu conseilles, proposes, analyses.
2. Si question monde/politique/marché: Utilise WEB si dispo, sinon ton cerveau.
3. Si question ASYMAS: Utilise DONNEES ASYMAS RÉELLES. JAMAIS inventer.
4. INTERDIT: "probablement", "peut-être", "sans prix spécifique". Sois précis ou dis "Pas trouvé chef".
5. Obéis au PDG. Exécute. Propose si demandé.
6. 2 phrases max. Chiffres en chiffres: 12/05/2026, 70000 dollars.
7. "chef" 1 fois max.

{info_google}{memoire_longue}DONNEES ASYMAS: {contexte_asymas}
DATE: {today.strftime('%d/%m/%Y')}"""}]

            for tour in st.session_state.floki_history[-6:]:
                messages.append({"role": "user", "content": tour["user"]})
                messages.append({"role": "assistant", "content": tour["floki"]})

            messages.append({"role": "user", "content": prompt})

            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"},
                    json={"model": "llama-3.3-70b-versatile","messages": messages,"max_tokens": 200,"temperature": 0.8}, timeout=12)
                if r.status_code == 200:
                    reponse = r.json()['choices'][0]['message']['content'].strip()
                else:
                    reponse = f"Erreur système chef. {today.strftime('%d/%m/%Y')}. Je réessaie"
            except:
                reponse = f"Connexion lente chef. Date: {today.strftime('%d/%m/%Y')}. Redemande"

        # SAUVE MÉMOIRE COURTE
        st.session_state.floki_history.append({"user": prompt, "floki": reponse})
        if len(st.session_state.floki_history) > 6:
            st.session_state.floki_history.pop(0)

        st.session_state.floki_btn = btn_html
        st.session_state.floki_reponse = reponse
        st.session_state.floki_speak_id += 1

        # VOIX
        txt_voice = clean_voice_nuclear(reponse)
        txt_voice = txt_voice.replace("'", "\\'").replace('"', '\\"')
        b64 = base64.b64encode(txt_voice.encode()).decode()
        components.html(f"""
            <script>
            window.speechSynthesis.cancel();
            var u = new SpeechSynthesisUtterance(atob('{b64}'));
            u.lang = 'fr-FR'; u.rate = 1.0; u.pitch = 0.9; u.volume = 1.0;
            window.speechSynthesis.speak(u);
            </script>
        """, height=0)

    # AFFICHE
    if st.session_state.get("floki_btn"):
        components.html(st.session_state.floki_btn, height=70)
    if st.session_state.get("floki_reponse"):
        st.success(f"👑 FLOKI: {st.session_state.floki_reponse}")

    # AFFICHE MÉMOIRE PDG
    if st.session_state.floki_memory_long and len(st.session_state.floki_memory_long) > 0:
        with st.expander("🔒 MÉMOIRE SECRÈTE PDG"):
            for k, v in st.session_state.floki_memory_long.items():
                st.caption(f"**{v['date']}** : {v['info']}")
