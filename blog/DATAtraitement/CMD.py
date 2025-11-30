import django_setup
django_setup.setup_django()

import pandas as pd
from utils import *
from blog.models import Plant, Famille, Article, AO, ISE, DA, Cde, Fournisseur, Appartenir_P_A, Appartenir_A_I, Appartenir_A_D, Appartenir_A_A, Commander
def process_cde_data (fichier) : 
    Commander.objects.all().delete()

    df_cmd_1 = pd.read_excel(fichier, sheet_name=0)
    df_cmd_2 = pd.read_excel(fichier, sheet_name=1)

    df_cmd_1.drop_duplicates(inplace=True) 
    df_cmd_2.drop_duplicates(inplace=True)  

    df_cmd = pd.merge(df_cmd_1, df_cmd_2, on="Commande")

    # Nettoyage des colonnes inutiles
    df_cmd = df_cmd.drop(columns=['AO_x','Fournissuer','Montant Commande TTC','Nombre de CODE'])
    pd.set_option('display.max_columns', None)
    print(df_cmd.head())

    # Nettoyage des formats
    for c in ['PU Commande', 'Qte Commande', 'Montant Commande']:
        df_cmd[c] = clean_decimal(df_cmd[c])

    for c in ['Commande', 'DA', 'ID ISE','AO_y', 'Fournisseur', 'CODE', 'Description', 'Udm', 'SF','Plant']:
        df_cmd[c] = clean_text(df_cmd[c])

    df_cmd['Date commande'] = clean_date(df_cmd['Date commande'])

    # Boucle sur chaque ligne
    for _, row in df_cmd.iterrows():
        try:
            cmd_value = row["Commande"]
            da_value = row["DA"]
            ao_value = row["AO_y"]

            # 1. PLANT
            plant_obj, _ = Plant.objects.get_or_create(code_plant=row["Plant"], defaults={"designation_plant": "inconnu"})

            # 2. FAMILLE
            famille_obj, _ = Famille.objects.get_or_create(designation_famille=row["SF"])

            # 3. ARTICLE
            article_obj, _ = Article.objects.get_or_create(
                code_article=row["CODE"],
                defaults={
                    "designation_article": row["Description"],
                    "udm": row["Udm"],
                    "famille": famille_obj
                }
            )

            # 4. LIEN PLANT <-> ARTICLE
            Appartenir_P_A.objects.get_or_create(plant=plant_obj, article=article_obj)

            # 5. AO (APPEL D'OFFRE)
            ao_obj = None
            if pd.notna(ao_value) and ao_value != "":
                ao_obj, _ = AO.objects.get_or_create(id_AO=ao_value)

            # 6. DA (DEMANDE D'ACHAT)
            da_obj = None
            if pd.notna(da_value):
                da_obj, _ = DA.objects.get_or_create(id_DA=da_value, defaults={"ao": ao_obj})
                # Si DA existe déjà sans AO, on l’associe
                if da_obj.ao is None and ao_obj is not None:
                    da_obj.ao = ao_obj
                    da_obj.save()

            # 7. CDE (COMMANDE)
            cde_obj, _ = Cde.objects.get_or_create(
                id_Cde=cmd_value,
                defaults={"ao": ao_obj}
            )

            # 8. FOURNISSEUR
            fournisseur_obj, _ = Fournisseur.objects.get_or_create(
                designation_Fournisseur=row["Fournisseur"]
            )

            # 9. ENREGISTRER LA RELATION COMMANDE (CORRECTION ICI ⬇️)
            # On utilise .create() pour forcer l'ajout de la ligne même si c'est le même article/commande
            # Cela permet d'avoir tes 14 lignes (doublons acceptés)
            Commander.objects.create(
                article=article_obj,
                cde=cde_obj,
                fournisseur=fournisseur_obj,
                montant_Cde=row["Montant Commande"],
                quantite_Cde=row["Qte Commande"],
                date_Cde=row["Date commande"]
            )

            print(f"Commande {cmd_value} : Ligne ajoutée ({row['CODE']})")

        except Exception as e:
            print(f"Erreur sur la ligne Commande {row.get('Commande', 'N/A')} : {e}")

    print(" Importation des Commandes terminée avec succès !")