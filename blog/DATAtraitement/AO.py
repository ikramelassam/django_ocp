import django_setup
django_setup.setup_django()

import pandas as pd
from utils import *
from blog.models import Plant, Famille, Article, AO, ISE, DA, Cde, Fournisseur, Appartenir_P_A, Appartenir_A_I, Appartenir_A_D, Appartenir_A_A, Commander
def process_ao_data(fichier):
    df_ao = pd.read_excel(fichier)  # 1 seule feuille
    df_ao.drop_duplicates(inplace=True) 

    df_ao["DA"] = clean_decimal(df_ao["DA"])
    df_ao["AO"] = clean_text(df_ao["AO"])
    df_ao['Date AO']=clean_date(df_ao['Date AO'])

    for _, row in df_ao.iterrows():
        try:
            da_value = row["DA"]
            ao_value = row["AO"]
            date_ao = row["Date AO"]

            ao_obj, _ = AO.objects.get_or_create(id_AO=ao_value)
            da_obj, _ = DA.objects.get_or_create(
                id_DA=da_value,
                defaults={
                    "ao": ao_obj }
                    )
            
            articles_da = Appartenir_A_D.objects.filter(da=da_obj)

            for art in articles_da:
                article_obj = art.article
                Appartenir_A_A.objects.update_or_create(
                    article=article_obj,
                    ao=ao_obj,
                    defaults={"date_AO": date_ao}
                )


        except DA.DoesNotExist:
            print(f"⚠️ DA {da_value} non trouvée pour AO {ao_value}")
        except Exception as e:
            print(f"⚠️ Erreur traitement AO {ao_value} et DA {da_value} : {e}")

    print("🎯 Importation du fichier AO terminée avec succès !")
