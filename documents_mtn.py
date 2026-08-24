"""Base documentaire du chatbot MTN.

Structure attendue pour chaque entrée :
- maladie : identifiant normalisé de la maladie
- categorie : catégorie du contenu (voir CATEGORIES_VALIDES)
- contenu : texte d'information
- source : source de référence (optionnel)
- date_maj : date de dernière mise à jour (optionnel)
"""

CATEGORIES_VALIDES = {
    "definition",
    "transmission",
    "symptomes",
    "signes_alerte",
    "prevention",
    "conduite",
    "facteurs_risque",
    "gravite",
    "gestes_interdits",
}

MALADIES_VALIDES = {
    "lepre",
    "dengue",
    "ems",
    "schistosomiase",
    "ulcere de buruli",
    "noma",
}

# Toutes les catégories autorisées sont obligatoires pour chaque maladie.
CATEGORIES_REQUISES = CATEGORIES_VALIDES.copy()


def valider_documents(documents=None):
    """Vérifie la structure et la cohérence de la base documentaire."""
    documents = documents or DOCUMENTS_MTN
    erreurs = []
    couverture = {}

    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            erreurs.append(f"Entrée {index}: n'est pas un dictionnaire")
            continue

        for key in ("maladie", "categorie", "contenu"):
            if key not in doc:
                erreurs.append(f"Entrée {index}: clé manquante '{key}'")

        if "maladie" in doc and doc["maladie"] not in MALADIES_VALIDES:
            erreurs.append(f"Entrée {index}: maladie inconnue '{doc['maladie']}'")

        if "categorie" in doc and doc["categorie"] not in CATEGORIES_VALIDES:
            erreurs.append(f"Entrée {index}: catégorie inconnue '{doc['categorie']}'")

        maladie = doc.get("maladie")
        if maladie:
            couverture.setdefault(maladie, set()).add(doc.get("categorie"))

    for maladie in sorted(MALADIES_VALIDES):
        categories = couverture.get(maladie, set())
        missing = sorted(CATEGORIES_REQUISES - categories)
        if missing:
            erreurs.append(
                f"{maladie}: catégories obligatoires absentes -> {', '.join(missing)}"
            )

    return {
        "erreurs": erreurs,
        "couverture": couverture,
    }


DOCUMENTS_MTN = [
    {
        "maladie": "lepre",
        "categorie": "definition",
        "contenu": """
La lèpre est une maladie infectieuse chronique causée par la bactérie Mycobacterium leprae.
Elle touche principalement la peau, les nerfs périphériques, les yeux et les muqueuses.
C'est une maladie tropicale négligée, mais elle reste curable si elle est détectée et traitée tôt.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "transmission",
        "contenu": """
La lèpre se transmet principalement par des gouttelettes respiratoires provenant d'une personne malade non traitée lors de contacts étroits et prolongés.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "symptomes",
        "contenu": """
Les signes les plus fréquents sont des taches cutanées avec perte de sensibilité, des engourdissements, une faiblesse musculaire et un épaississement des nerfs périphériques.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "signes_alerte",
        "contenu": """
Consultez rapidement un centre de santé si vous présentez :
- des taches avec perte de sensibilité ;
- un engourdissement des mains ou des pieds ;
- une faiblesse musculaire ;
- un gonflement des nerfs.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "prevention",
        "contenu": """
Pour prévenir la lèpre :
- détecter précocement les cas suspects ;
- traiter rapidement les personnes atteintes ;
- surveiller les contacts proches ;
- sensibiliser la communauté ;
- signaler les cas suspects aux agents de santé.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "conduite",
        "contenu": """
En cas de suspicion de lèpre :
- rendez-vous rapidement dans un centre de santé ;
- évitez le retard de consultation ;
- suivez le traitement prescrit jusqu'à son terme.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "facteurs_risque",
        "contenu": """
Les personnes les plus exposées sont celles vivant dans des zones où la lèpre est présente, les contacts proches d'un cas non traité, ainsi que les personnes vivant dans des conditions de pauvreté et de surpopulation.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "lepre",
        "categorie": "gravite",
        "contenu": """
Si elle n'est pas traitée, la lèpre peut entraîner des lésions permanentes des nerfs, des handicaps, des déformations et des complications cutanées durables.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "definition",
        "contenu": """
La dengue est une maladie virale transmise par les moustiques Aedes infectés. Elle est fréquente dans les zones tropicales et subtropicales et peut évoluer vers des formes graves si elle n'est pas prise en charge rapidement.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "transmission",
        "contenu": """
La dengue se transmet par la piqûre d'un moustique Aedes infecté. Elle ne se transmet généralement pas directement d'une personne à une autre.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "symptomes",
        "contenu": """
La dengue provoque habituellement :
- une forte fièvre ;
- des maux de tête ;
- des douleurs musculaires ;
- des douleurs articulaires ;
- des nausées ;
- des éruptions cutanées.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "signes_alerte",
        "contenu": """
Consultez rapidement un centre de santé si vous présentez :
- des saignements ;
- des douleurs abdominales importantes ;
- des vomissements persistants ;
- une difficulté respiratoire ;
- une grande faiblesse.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "gravite",
        "contenu": """
La dengue grave peut entraîner des hémorragies, une défaillance circulatoire, une détresse respiratoire et parfois le décès si le traitement est retardé.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "prevention",
        "contenu": """
Pour prévenir la dengue :
- éliminer les eaux stagnantes ;
- utiliser des répulsifs ;
- porter des vêtements couvrants ;
- se protéger contre les piqûres de moustiques ;
- utiliser des moustiquaires.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "conduite",
        "contenu": """
En cas de suspicion de dengue :
- consultez rapidement un centre de santé ;
- buvez beaucoup d'eau ;
- évitez l'automédication sans avis médical.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "dengue",
        "categorie": "facteurs_risque",
        "contenu": """
Les personnes les plus exposées sont celles vivant dans des zones urbaines ou périurbaines, près d'eaux stagnantes et de habitats favorables au moustique Aedes.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "definition",
        "contenu": """
Les envenimations par morsure de serpent (EMS) surviennent lorsqu'un serpent venimeux injecte son venin lors d'une morsure. C'est une urgence médicale dans de nombreuses zones rurales.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "transmission",
        "contenu": """
Les EMS surviennent à la suite d'une morsure de serpent venimeux. Elles ne se transmettent pas d'une personne à une autre.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "facteurs_risque",
        "contenu": """
Les morsures surviennent surtout lors de travaux agricoles, de ramassage du bois, de chasse, de déplacements en brousse ou de cueillette de fruits.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "symptomes",
        "contenu": """
Les signes les plus fréquents sont la douleur, le gonflement, la rougeur, un saignement au niveau de la morsure et parfois des cloques ou des plaies.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "signes_alerte",
        "contenu": """
Consultez immédiatement un centre de santé si vous observez :
- un gonflement important ;
- des saignements ;
- des difficultés respiratoires ;
- une chute des paupières ;
- une faiblesse musculaire ;
- une perte de connaissance.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "gravite",
        "contenu": """
Une envenimation grave peut provoquer des hémorragies, une paralysie, une détresse respiratoire, une insuffisance rénale et le décès si elle n'est pas prise en charge rapidement.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "conduite",
        "contenu": """
En cas de morsure de serpent :
- gardez votre calme ;
- immobilisez le membre atteint ;
- conduisez immédiatement la victime dans un centre de santé ;
- ne retardez pas la consultation.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "gestes_interdits",
        "contenu": """
Il ne faut pas :
- poser un garrot ;
- couper ou scarifier la peau ;
- essayer d'aspirer le venin ;
- brûler la plaie ;
- appliquer des produits traditionnels.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ems",
        "categorie": "prevention",
        "contenu": """
Pour prévenir les morsures :
- porter des chaussures fermées ;
- éviter les trous ou les pierres sans vérification ;
- utiliser une lampe la nuit ;
- débroussailler les sentiers.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "definition",
        "contenu": """
La schistosomiase, également appelée bilharziose, est une maladie parasitaire causée par des vers appelés schistosomes. Elle touche surtout les populations vivant près des eaux douces contaminées.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "transmission",
        "contenu": """
La schistosomiase se transmet lors du contact avec de l'eau douce contaminée par des larves libérées par des escargots infectés.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "symptomes",
        "contenu": """
Les symptômes peuvent inclure du sang dans les urines, du sang dans les selles, des douleurs abdominales, des brûlures à la miction, des diarrhées et une fatigue importante.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "signes_alerte",
        "contenu": """
Consultez rapidement un centre de santé si vous observez du sang dans les urines ou les selles, des douleurs abdominales persistantes ou une fatigue inhabituelle.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "prevention",
        "contenu": """
Pour prévenir la schistosomiase :
- éviter les eaux suspectes ;
- utiliser des latrines ;
- protéger les enfants contre les baignades dans les eaux contaminées ;
- participer aux campagnes de dépistage et de traitement.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "conduite",
        "contenu": """
Si vous pensez avoir la schistosomiase :
- rendez-vous rapidement dans un centre de santé ;
- faites les examens demandés ;
- prenez le traitement prescrit jusqu'à la fin.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "facteurs_risque",
        "contenu": """
Les personnes les plus exposées sont celles qui vivent ou travaillent près des rivières, lacs, marigots ou zones d'irrigation, ainsi que les enfants et les pêcheurs.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "schistosomiase",
        "categorie": "gravite",
        "contenu": """
Sans traitement, la schistosomiase peut provoquer des complications digestives, urinaires, une anémie, un retard de croissance et des difficultés de développement chez l'enfant.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "definition",
        "contenu": """
L'ulcère de Buruli est une infection chronique de la peau et des tissus sous-cutanés causée par Mycobacterium ulcerans. La maladie est particulièrement associée aux zones humides.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "transmission",
        "contenu": """
Le mode exact de transmission de l'ulcère de Buruli n'est pas encore complètement élucidé, mais la maladie est associée aux environnements humides, aux marécages et aux eaux stagnantes.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "symptomes",
        "contenu": """
Les premiers signes sont souvent un nodule indolore, une plaque dure, un gonflement localisé ou un œdème d'un membre. À un stade avancé, une plaie ouverte ou un ulcère étendu peut apparaître.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "signes_alerte",
        "contenu": """
Consultez rapidement si vous observez une boule indolore sous la peau, un gonflement qui augmente de taille, une plaque dure persistante ou une plaie qui ne guérit pas.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "gravite",
        "contenu": """
Sans traitement, l'ulcère de Buruli peut provoquer de vastes plaies, des cicatrices importantes, des limitations de mouvement, des déformations et des handicaps permanents.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "prevention",
        "contenu": """
Pour réduire les conséquences :
- surveillez toute lésion inhabituelle de la peau ;
- nettoyez correctement les plaies ;
- protégez les blessures contre les infections ;
- consultez rapidement en cas de nodule, plaque ou gonflement anormal.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "conduite",
        "contenu": """
Si vous pensez souffrir d'un ulcère de Buruli :
- rendez-vous rapidement dans un centre de santé ;
- ne percez pas la lésion ;
- évitez les traitements traditionnels sur la plaie ;
- respectez le traitement prescrit jusqu'à la fin.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "facteurs_risque",
        "contenu": """
Les personnes vivant près des zones humides, des marécages, des rivières, des lacs ou des eaux stagnantes sont plus exposées.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "ulcere de buruli",
        "categorie": "gestes_interdits",
        "contenu": """
Il ne faut pas percer la lésion, utiliser des produits traditionnels sur la plaie ou attendre trop longtemps avant consultation.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-08",
    },
    {
        "maladie": "noma",
        "categorie": "definition",
        "contenu": """
Le noma est une maladie infectieuse grave qui détruit rapidement les tissus de la bouche et du visage.
Il touche surtout les enfants fragilisés par la malnutrition ou une autre maladie et nécessite une prise en charge médicale urgente.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-23",
    },
    {
        "maladie": "noma",
        "categorie": "transmission",
        "contenu": """
Le noma n'est pas considéré comme une maladie contagieuse. Il survient surtout chez des personnes fragilisées lorsque des bactéries présentes dans la bouche profitent d'une mauvaise santé générale.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-23",
    },
    {
        "maladie": "noma",
        "categorie": "symptomes",
        "contenu": """
Les signes du noma peuvent inclure une inflammation des gencives, une douleur ou une mauvaise haleine, puis une lésion qui s'étend rapidement dans la bouche et le visage.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-23",
    },
    {
        "maladie": "noma",
        "categorie": "prevention",
        "contenu": """
La prévention du noma repose sur une alimentation suffisante, une bonne hygiène bucco-dentaire, l'accès aux soins et le traitement rapide des infections et de la malnutrition.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-23",
    },
    {
        "maladie": "noma",
        "categorie": "conduite",
        "contenu": """
Toute lésion ou inflammation qui progresse rapidement dans la bouche ou le visage doit être considérée comme une urgence. Consultez immédiatement un professionnel de santé.
""",
        "source": "OMS / guide de santé publique",
        "date_maj": "2026-08-23",
    },
]
