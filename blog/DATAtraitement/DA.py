import django_setup
django_setup.setup_django()

import pandas as pd
from utils import *
from blog.models import Plant, Famille, Article, AO, ISE, DA, Cde, Fournisseur, Appartenir_P_A, Appartenir_A_I, Appartenir_A_D, Appartenir_A_A, Commander
def process_da_data(fichier):
    df_da_1 = pd.read_excel(fichier, sheet_name=0)
    df_da_2 = pd.read_excel(fichier, sheet_name=1)


    df_da_1.drop_duplicates(inplace=True)
    df_da_2.drop_duplicates(inplace=True)  

    df_da = pd.merge(df_da_1, df_da_2, on="DA")

    # juste pour test
    #pd.set_option('display.max_columns', None)
    #   print(df_da.head())

    df_da =df_da.drop(columns=['AO_x','SF_x','Nombre de CODE','Montant DA'])
    pd.set_option('display.max_columns', None)
    print(df_da.head())

    # Supprimer les espaces et caractères spéciaux, puis convertir en Decimal
    for c in ['Montant', 'PUMP', 'Qte DA']:
        df_da[c] = clean_decimal(df_da[c])

    for c in ['DA', 'ID ISE', 'AO_y','Plant', 'Description', 'CODE', 'Déstination', 'Udm', 'SF_y']:
        df_da[c] = clean_text(df_da[c])

    df_da['Date DA']=clean_date(df_da['Date DA'])

    for _, row in df_da.iterrows():
        try:
            id_da = row['DA']
            id_ao = row["AO_y"] if pd.notna(row["AO_y"]) else None


            ao_obj = None
            if id_ao:
                ao_obj, _ = AO.objects.get_or_create(id_AO=id_ao)

            da_obj, _ = DA.objects.get_or_create(
                id_DA=id_da,
                defaults={
                    "ao": ao_obj }
                    )
            
            famille_obj, _ = Famille.objects.get_or_create(
                designation_famille=row["SF_y"]
            )

            article_obj, _ = Article.objects.get_or_create(
                code_article=row["CODE"],
                defaults={
                    "designation_article": row["Description"],
                    "udm": row["Udm"],
                    "famille": famille_obj
                }
            )
            Appartenir_A_A.objects.get_or_create(
                    article=article_obj,
                    ao=ao_obj,
                    defaults={"date_AO": "1900-01-01"}
                )

            
            plant_obj, _ = Plant.objects.get_or_create(
                code_plant=row["Plant"],
                defaults={"designation_plant": "inconnu"}
            )

            
            Appartenir_P_A.objects.get_or_create(
                plant=plant_obj,
                article=article_obj
            )
            
            Appartenir_A_D.objects.get_or_create(
                article=article_obj,
                da=da_obj,
                defaults={
                    "montant_DA": row["Montant"],
                    "date_DA": row['Date DA'],
                    "quantite_DA": row["Qte DA"],
                    "destination": row["Déstination"]
                }

            )

        except Exception as e:
            print(f"Erreur ligne DA {row.get('DA', 'inconnue')} : {e}")
        print(" Importation du fichier DA terminée avec succès !")