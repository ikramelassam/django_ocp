from django.shortcuts import render, get_object_or_404
from .DATAtraitement.services import data_service  # Import du singleton
from .models import ISE, Article, Appartenir_A_I, Appartenir_A_D, Appartenir_A_A, Commander, Appartenir_P_A
from datetime import datetime


def recherche_view(request):
    context = {}
    
    if request.method == "POST":
        type_choix = request.POST.get('type_doc') # 'ISE', 'DA', etc.
        code_input = request.POST.get('code_input')

        if type_choix and code_input:
            # APPEL CENTRALISÉ : La vue ne sait pas comment on cherche, elle demande juste au service
            df_resultat = data_service.search_info(type_choix, code_input)

            if df_resultat is not None and not df_resultat.empty:
                # Conversion du DataFrame en HTML pour l'affichage
                html_table = df_resultat.to_html(classes='table table-bordered', index=False)
                
                # Calcul des sommes (si les colonnes existent)
                total_ise = df_resultat['Mnt ISE'].sum() if 'Mnt ISE' in df_resultat.columns else 0
                total_da = df_resultat['Mnt DA'].sum() if 'Mnt DA' in df_resultat.columns else 0
                total_cmd = df_resultat['Mnt CMD'].sum() if 'Mnt CMD' in df_resultat.columns else 0

                context = {
                    'resultat': html_table,
                    'totaux': {'ise': total_ise, 'da': total_da, 'cmd': total_cmd},
                    'code_rech': code_input,
                    'type_rech': type_choix
                }
            else:
                context['error'] = f"Aucun résultat trouvé pour {type_choix} : {code_input}"
        else:
            context['error'] = "Veuillez remplir tous les champs."

    return render(request, 'blog/recherche_interface.html', context)
def dashboard_view(request):
    # Pour l'instant on retourne juste le template statique
    return render(request, 'blog/dashboard.html')
def suivi_view(request):
    context = {}
    
    # Si on appuie sur "Rechercher"
    if request.method == "POST":
        type_choix = request.POST.get('type_doc') # Vient de l'input caché
        code_input = request.POST.get('code_input')

        if type_choix and code_input:
            # Appel au service centralisé (le même qu'avant !)
            df_resultat = data_service.search_info(type_choix, code_input)

            if df_resultat is not None and not df_resultat.empty:
                # On transforme en HTML propre pour l'intégration
                # classes='...' permet d'appliquer du style CSS si besoin
                html_table = df_resultat.to_html(classes='table-result', index=False, border=0)
                
                context = {
                    'resultat': html_table,
                    'code_rech': code_input,
                    'type_rech': type_choix
                }
            else:
                context['error'] = f"Aucune donnée trouvée pour {type_choix} : {code_input}"
    
    return render(request, 'blog/suivi_demandes.html', context)



def detail_flux(request, id_flux, id_ise, id_da, id_ao, id_cmd):
    
    # 0. Récupération optionnelle de l'article pour le titre
    article_obj = Article.objects.filter(code_article=id_flux).first()

    # --- 1. GESTION DE L'ISE ---
    date_ise = None
    montant_ise = 0
    destination_val = '-'
    udm = 'N/A'
    
    if id_ise and id_ise not in ['0', 'N/A']:
        objet_ise = Appartenir_A_I.objects.filter(
            ise__id_ise=id_ise,
            article__code_article=id_flux
        ).select_related('article').first()
        
        if objet_ise:
            date_ise = objet_ise.date_ise 
            montant_ise = objet_ise.montant_ise * objet_ise.quantite_ise
            destination_val = objet_ise.destination
            udm_val = article_obj.udm

    # --- 2. GESTION DE LA DA ---
    date_da = None
    montant_da = 0
    
    if id_da and id_da not in ['0', 'N/A']:
        objet_da = Appartenir_A_D.objects.filter(
            da__id_DA=id_da,
            article__code_article=id_flux
        ).select_related('da').first()
        
        if objet_da:
            date_da = objet_da.date_DA 
            montant_da = objet_da.montant_DA * objet_da.quantite_DA if hasattr(objet_da, 'montant_DA') else 0

    # --- 3. GESTION DE L'AO ---
    date_ao = None
    
    if id_ao and id_ao not in ['0', 'N/A']:
        objet_ao = Appartenir_A_A.objects.filter(
            ao__id_AO=id_ao,
            article__code_article=id_flux
        ).select_related('ao').first()
        
        if objet_ao:
            date_ao = objet_ao.date_AO

    # --- 4. GESTION DE LA COMMANDE (NOUVEAU BLOC) ---
    date_cmd = None
    montant_cmd = 0
    fournisseur_nom = '-'

    if id_cmd and id_cmd not in ['0', 'N/A']:
        objet_cmd = Commander.objects.filter(
            cde__id_Cde=id_cmd,
            article__code_article=id_flux
        ).select_related('cde', 'fournisseur').first()

        if objet_cmd:
            date_cmd = objet_cmd.date_Cde
            montant_cmd = objet_cmd.montant_Cde * objet_cmd.quantite_Cde
            if objet_cmd.fournisseur:
                fournisseur_nom = objet_cmd.fournisseur.designation_Fournisseur
    code_plant = 'N/A'
    nom_plant = 'Non spécifié'

    # On cherche le Plant lié à cet article
    objet_plant = Appartenir_P_A.objects.filter(
        article__code_article=id_flux
    ).select_related('plant').first()

    if objet_plant and objet_plant.plant:
        code_plant = objet_plant.plant.code_plant
        # On vérifie si le champ s'appelle designation_plant ou designation_Plant
        if hasattr(objet_plant.plant, 'designation_plant'):
            nom_plant = objet_plant.plant.designation_plant
        elif hasattr(objet_plant.plant, 'designation_Plant'):
            nom_plant = objet_plant.plant.designation_plant
    article_obj = Article.objects.filter(code_article=id_flux).select_related('famille').first()

    # On prépare la variable SF pour le contexte
    sf_article = 'Non défini'
    if article_obj and article_obj.famille:
        sf_article = article_obj.famille.designation_famille 
    if montant_cmd == 0:
        ecart_total = 0
    else : 
        ecart_total = montant_cmd - montant_ise
    taux_realisation = (montant_cmd / montant_ise) * 100 if montant_ise > 0 else 0
    def calculer_delai_jours(date_debut, date_fin):
        """Calcule le nombre de jours entre deux dates"""
        if not date_debut or not date_fin:
            return 0
        
        try:
            delta = date_fin - date_debut
            return abs(delta.days)
        except:
            return 0  
    delai_ise_da = calculer_delai_jours(date_ise, date_da)
    delai_da_ao = calculer_delai_jours(date_da, date_ao)
    delai_ao_cmd = calculer_delai_jours(date_ao, date_cmd)

    # Délai total (seulement si toutes les dates sont disponibles)
    if date_ise and date_cmd:
        delai_total = calculer_delai_jours(date_ise, date_cmd)
    else:
        delai_total = 0
    # --- 5. CONTEXTE ---
    context = {
        # ISE
        'ise': { 'id_ise': id_ise if id_ise != '0' else 'N/A' },
        'rel_ise': { 'date_ise': date_ise, 'montant_ise': montant_ise },

        # DA
        'rel_da': {
            'da': { 'id_DA': id_da if id_da != '0' else 'N/A' },
            'date_DA': date_da,
            'montant_DA': montant_da
        },

        # AO
        'rel_ao': {
            'ao': { 'id_AO': id_ao if id_ao != '0' else 'N/A' },
            'date_AO': date_ao,
        },

        # Commande (Maintenant dynamique)
        'rel_cmd': {
            'cde': { 'id_Cde': id_cmd if id_cmd != '0' else 'En attente' },
            'date_Cde': date_cmd,
            'montant_Cde': montant_cmd,
            'fournisseur': { 'designation_Fournisseur': fournisseur_nom }
        },

        # Article
        'article': {
            'code_article': id_flux,
            'designation_article': article_obj.designation_article if article_obj else 'Article Inconnu',
            'famille': sf_article,
            'destination': destination_val,
            'udm': udm_val
        },

        'rel_plant': {
            'plant': { 'code_plant': code_plant , 'designation_plant': nom_plant  }
        },
        'ecart_total': ecart_total,
        'taux_realisation': taux_realisation,
        'delai_ise_da': delai_ise_da,
        'delai_da_ao': delai_da_ao,
        'delai_ao_cmd': delai_ao_cmd,
        'delai_total': delai_total,
    }
    
    return render(request, 'blog/detail_flux.html', context)