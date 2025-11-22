import django_setup
django_setup.setup_django()
from utils import *
from blog.models import Plant, Famille, Article, AO, ISE, DA, Appartenir_P_A, Appartenir_A_I

fichier = "C:/OCP/Demande ISE.xlsx"
df_besoin_1 = pd.read_excel(fichier, sheet_name=0)
df_besoin_2 = pd.read_excel(fichier, sheet_name=1)

df_besoin_1.drop_duplicates(inplace=True) 
df_besoin_2.drop_duplicates(inplace=True) 
df_besoin = pd.merge(df_besoin_1, df_besoin_2, on="ID ISE")
# juste pour test
# #pd.set_option('display.max_columns', None)
# #print(df_besoin.head())
df_besoin =df_besoin.drop(columns=['DA_x','plant_x','designation plant_x','Nombre de Code','Montant ISE_x'])
pd.set_option('display.max_columns', None)

print(df_besoin.head())
# Supprimer les espaces et caractères spéciaux, puis convertir en Decimal
for c in ['Qte ISE', 'Montant ISE_y', 'PUMP']:
    df_besoin[c] = clean_decimal(df_besoin[c])

for c in ['ID ISE', 'DA_y','plant_y', 'designation plant_y', 'Code', 'Désignaion', 'Udm', 'SF', 'Déstination']:
    df_besoin[c] = clean_text(df_besoin[c])
    df_besoin['Date ISE']=clean_date(df_besoin['Date ISE'])

for _, row in df_besoin.iterrows():
    try:
    
        da_value = row["DA_y"]  

        da_obj = None
        if pd.notna(da_value):  
            da_obj, _ = DA.objects.get_or_create(
                id_DA=da_value,
                defaults={"ao": None}  
            )

        ise_obj, exist_ise = ISE.objects.get_or_create(
            id_ise=row["ID ISE"],
            defaults={"da": da_obj}  
        )

        if not exist_ise and da_obj is not None and ise_obj.da is None:
            ise_obj.da = da_obj
            ise_obj.save()

        
        famille_obj, _ = Famille.objects.get_or_create(
            designation_famille=row["SF"]
        )

        article_obj, _ = Article.objects.get_or_create(
            code_article=row["Code"],
            defaults={
                "designation_article": row["Désignaion"],
                "udm": row["Udm"],
                "famille": famille_obj
            }
        )

        plant_obj, _ = Plant.objects.get_or_create(
            code_plant=row["plant_y"],
            defaults={"designation_plant": row["designation plant_y"]}
        )

        Appartenir_P_A.objects.get_or_create(
            plant=plant_obj,
            article=article_obj
        )

        # relation Article ↔ ISE et da
        Appartenir_A_I.objects.get_or_create(
            article=article_obj,
            ise=ise_obj,
            defaults={
                "montant_ise": row["Montant ISE_y"],
                "date_ise": row['Date ISE'],
                "quantite_ise": row["Qte ISE"],
                "destination": row["Déstination"]
            }
        )


    except Exception as e:
        print(f" Erreur à la ligne ISE {row.get('ID ISE', 'Inconnue')}: {e}")
