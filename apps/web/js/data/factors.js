// Food footprints, kg CO2e per kg of product, whole supply chain (farm to retail).
// Tier 1 (international): Poore & Nemecek (2018), Science 360:987, mean values as published by Our World in Data.
// Means sit above medians, which keeps estimates on the high side.
export const PN_SOURCE = 'Poore & Nemecek (2018), Science — global supply-chain study';

export const FOOD_FACTORS = {
  beef: 99.48, lamb: 39.72, cheese: 23.88, coffee: 28.53, chocolate: 46.65, prawns: 26.87, fish: 13.63,
  pork: 12.31, poultry: 9.87, palmOil: 7.32, oliveOil: 5.42, soyOil: 6.32, rapeseedOil: 3.77, sunflowerOil: 3.60,
  eggs: 4.67, rice: 4.45, caneSugar: 3.20, tofu: 3.16, milk: 3.15, groundnuts: 3.23, oatmeal: 2.48, tomatoes: 2.09,
  pulses: 1.79, wine: 1.79, wheat: 1.57, berries: 1.53, beer: 1.18, plantMilk: 0.98, peas: 0.98, bananas: 0.86,
  brassicas: 0.51, potatoes: 0.46, apples: 0.43, citrus: 0.39, rootVeg: 0.43,
};

// Matching rules: first rule whose pattern matches the product's category hint or tags wins.
// `x` multiplies the factor where the product is a concentrate of the raw food (e.g. ~2.6 kg beans per kg instant coffee).
export const FOOD_RULES = [
  { re: /oat-based|plant-based-milk|soy-milk|almond-milk|plant-based-drink/, key: 'plantMilk' },
  { re: /beef|veal/, key: 'beef' },
  { re: /lamb|mutton/, key: 'lamb' },
  { re: /instant-coffee|soluble/, key: 'coffee', x: 2.6 },
  { re: /coffee/, key: 'coffee' },
  { re: /chocolate|cocoa/, key: 'chocolate' },
  { re: /prawn|shrimp/, key: 'prawns' },
  { re: /salmon|fish|tuna|cod|seafood/, key: 'fish' },
  { re: /bacon|pork|ham|sausage/, key: 'pork' },
  { re: /chicken|poultry|turkey/, key: 'poultry' },
  { re: /cheese|cheddar/, key: 'cheese' },
  { re: /yogurt|yoghurt|skyr/, key: 'milk', x: 1.2 },
  { re: /\beggs?\b|en:eggs/, key: 'eggs' },
  { re: /olive-oil/, key: 'oliveOil' },
  { re: /palm-oil/, key: 'palmOil' },
  { re: /rapeseed|canola/, key: 'rapeseedOil' },
  { re: /sunflower-oil/, key: 'sunflowerOil' },
  { re: /rice/, key: 'rice' },
  { re: /sugar/, key: 'caneSugar' },
  { re: /tofu/, key: 'tofu' },
  { re: /peanut|groundnut/, key: 'groundnuts' },
  { re: /\bmilks?\b|semi-skimmed|whole-milk|skimmed-milk/, key: 'milk' },
  { re: /oat|porridge|cereal|muesli/, key: 'oatmeal' },
  { re: /wine/, key: 'wine' },
  { re: /beer|lager|\bales?\b/, key: 'beer' },
  { re: /tomato/, key: 'tomatoes' },
  { re: /baked-beans|pulse|lentil|chickpea|beans/, key: 'pulses' },
  { re: /bread|pasta|lasagne|wheat|flour|biscuit/, key: 'wheat' },
  { re: /\bpeas\b|green-peas|frozen-peas/, key: 'peas' },
  { re: /banana/, key: 'bananas' },
  { re: /apple-juice/, key: 'apples', x: 2 },
  { re: /apple/, key: 'apples' },
  { re: /orange-juice|citrus-juice/, key: 'citrus', x: 2 },
  { re: /orange|citrus|lemon/, key: 'citrus' },
  { re: /berr|grape/, key: 'berries' },
  { re: /potato|crisps|chips|hash-brown/, key: 'potatoes' },
];

// Tier 4 educated guesses. Deliberately high; CONFIG.estimateUplift is applied on top.
// perKg: kg CO2e per kg of product. perItem: kg CO2e per item where weight is not meaningful.
export const ESTIMATE_GROUPS = [
  { id: 'meat', label: 'Meat or fish', perKg: 30 },
  { id: 'dairy', label: 'Dairy (cheese, butter, cream)', perKg: 12 },
  { id: 'sweets', label: 'Sweets, snacks, desserts', perKg: 6 },
  { id: 'ready', label: 'Ready meal', perKg: 6 },
  { id: 'plant', label: 'Fruit, veg, bread, grains', perKg: 2 },
  { id: 'drinks', label: 'Soft drinks, juice, water', perKg: 1.5 },
  { id: 'tea', label: 'Tea or coffee (dry, unbrewed)', perKg: 10 },
  { id: 'food', label: 'Other food', perKg: 5 },
  { id: 'toiletries', label: 'Toiletries (shampoo, soap, toothpaste)', perItem: 0.8 },
  { id: 'cleaning', label: 'Cleaning products', perItem: 1.2 },
  { id: 'paper', label: 'Toilet roll, kitchen roll, tissues', perItem: 1.5 },
  { id: 'clothing', label: 'Clothing item', perItem: 10 },
  { id: 'electrical', label: 'Small electrical item', perItem: 25 },
  { id: 'other', label: 'Other household item', perItem: 3 },
];

// Category tags that suggest a tier-4 group when no tier-1/2 figure exists.
export const GROUP_RULES = [
  { re: /\btea|teas\b|tea-bags|infusion/, id: 'tea' },
  { re: /beverage|drink|soda|cola|water|juice/, id: 'drinks' },
  { re: /meat|fish|poultry/, id: 'meat' }, { re: /dairy|butter|cream/, id: 'dairy' },
  { re: /sweet|snack|confection|biscuit|cake|dessert/, id: 'sweets' }, { re: /meal|pizza/, id: 'ready' },
  { re: /fruit|vegetable|bread|cereal|grain/, id: 'plant' },
];

// Agribalyse gives some products per kg of the prepared drink, not the dry product. Skip it for these.
export const AGRIBALYSE_SKIP = /\btea|teas\b|tea-bags|infusion|instant-coffee|soluble/;
