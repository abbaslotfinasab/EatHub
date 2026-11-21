"""Framework-independent choice values shared by Catalog adapters and API contracts."""

PRODUCT_STATUS_DRAFT = "draft"
PRODUCT_STATUS_ACTIVE = "active"
PRODUCT_STATUS_ARCHIVED = "archived"
PRODUCT_STATUS_CHOICES = (
    (PRODUCT_STATUS_DRAFT, "Draft"),
    (PRODUCT_STATUS_ACTIVE, "Active"),
    (PRODUCT_STATUS_ARCHIVED, "Archived"),
)

ALLERGEN_CELERY = "celery"
ALLERGEN_CEREALS_GLUTEN = "cereals_gluten"
ALLERGEN_CRUSTACEANS = "crustaceans"
ALLERGEN_EGGS = "eggs"
ALLERGEN_FISH = "fish"
ALLERGEN_LUPIN = "lupin"
ALLERGEN_MILK = "milk"
ALLERGEN_MOLLUSCS = "molluscs"
ALLERGEN_MUSTARD = "mustard"
ALLERGEN_PEANUTS = "peanuts"
ALLERGEN_SESAME = "sesame"
ALLERGEN_SOYBEANS = "soybeans"
ALLERGEN_SULPHITES = "sulphites"
ALLERGEN_TREE_NUTS = "tree_nuts"
ALLERGEN_CODE_CHOICES = (
    (ALLERGEN_CELERY, "Celery"),
    (ALLERGEN_CEREALS_GLUTEN, "Cereals containing gluten"),
    (ALLERGEN_CRUSTACEANS, "Crustaceans"),
    (ALLERGEN_EGGS, "Eggs"),
    (ALLERGEN_FISH, "Fish"),
    (ALLERGEN_LUPIN, "Lupin"),
    (ALLERGEN_MILK, "Milk"),
    (ALLERGEN_MOLLUSCS, "Molluscs"),
    (ALLERGEN_MUSTARD, "Mustard"),
    (ALLERGEN_PEANUTS, "Peanuts"),
    (ALLERGEN_SESAME, "Sesame"),
    (ALLERGEN_SOYBEANS, "Soybeans"),
    (ALLERGEN_SULPHITES, "Sulphur dioxide and sulphites"),
    (ALLERGEN_TREE_NUTS, "Tree nuts"),
)

ALLERGEN_PRESENCE_CONTAINS = "contains"
ALLERGEN_PRESENCE_MAY_CONTAIN = "may_contain"
ALLERGEN_PRESENCE_CHOICES = (
    (ALLERGEN_PRESENCE_CONTAINS, "Contains"),
    (ALLERGEN_PRESENCE_MAY_CONTAIN, "May contain"),
)

DIETARY_TAG_VEGAN = "vegan"
DIETARY_TAG_VEGETARIAN = "vegetarian"
DIETARY_TAG_GLUTEN_FREE = "gluten_free"
DIETARY_TAG_DAIRY_FREE = "dairy_free"
DIETARY_TAG_HALAL = "halal"
DIETARY_TAG_KOSHER = "kosher"
DIETARY_TAG_CODE_CHOICES = (
    (DIETARY_TAG_VEGAN, "Vegan"),
    (DIETARY_TAG_VEGETARIAN, "Vegetarian"),
    (DIETARY_TAG_GLUTEN_FREE, "Gluten-free"),
    (DIETARY_TAG_DAIRY_FREE, "Dairy-free"),
    (DIETARY_TAG_HALAL, "Halal"),
    (DIETARY_TAG_KOSHER, "Kosher"),
)
