// UK Government GHG conversion factors (DESNZ/DEFRA 2025), kg CO2e per passenger-km unless noted.
// Flights include radiative forcing (the higher, fuller figure). Cars are per vehicle-km, split by passengers.
export const TRAVEL_SOURCE = 'UK Government GHG conversion factors 2025 (DESNZ)';
export const FLIGHT_UPLIFT = 1.08; // distance uplift for routing and holding, as recommended in the UK factors

export const FLIGHT = {
  domestic: { economy: 0.229, business: 0.229 },
  short: { economy: 0.126, business: 0.189 },
  long: { economy: 0.117, business: 0.339 },
};

export const GROUND = [
  { id: 'petrol', label: 'Petrol car', perKm: 0.16272, perVehicle: true },
  { id: 'diesel', label: 'Diesel car', perKm: 0.17304, perVehicle: true },
  { id: 'ev', label: 'Electric car', perKm: 0.05, perVehicle: true, note: 'estimate on UK grid, rounded up' },
  { id: 'rail', label: 'Train (UK national rail)', perKm: 0.03546 },
  { id: 'bus', label: 'Local bus', perKm: 0.10385 },
  { id: 'coach', label: 'Coach', perKm: 0.02776 },
  { id: 'ferry', label: 'Ferry (foot passenger)', perKm: 0.01871 },
];

// Home energy, kg CO2e per kWh. Electricity uses the UK grid factor with losses, rounded up.
export const ENERGY = { electricity: 0.23, gas: 0.19 };

// Typical meals, kg CO2e per serving, built from the Poore & Nemecek food factors.
export const MEALS = [
  { id: 'beef', label: 'Beef meal (150 g beef)', kg: 15.6 },
  { id: 'lamb', label: 'Lamb meal (150 g lamb)', kg: 6.4 },
  { id: 'pork', label: 'Pork meal', kg: 2.3 },
  { id: 'chicken', label: 'Chicken meal', kg: 2.0 },
  { id: 'fish', label: 'Fish meal', kg: 2.6 },
  { id: 'veggie', label: 'Vegetarian meal', kg: 1.2 },
  { id: 'vegan', label: 'Vegan meal', kg: 0.7 },
];

export const AIRPORTS = [
  ['LHR', 'London Heathrow', 51.47, -0.454], ['LGW', 'London Gatwick', 51.148, -0.19], ['MAN', 'Manchester', 53.354, -2.275],
  ['EDI', 'Edinburgh', 55.95, -3.363], ['GLA', 'Glasgow', 55.872, -4.433], ['BHX', 'Birmingham', 52.454, -1.748],
  ['BRS', 'Bristol', 51.383, -2.719], ['BFS', 'Belfast', 54.657, -6.216], ['DUB', 'Dublin', 53.421, -6.27],
  ['CDG', 'Paris', 49.01, 2.548], ['AMS', 'Amsterdam', 52.31, 4.768], ['FRA', 'Frankfurt', 50.033, 8.57],
  ['MAD', 'Madrid', 40.472, -3.561], ['BCN', 'Barcelona', 41.297, 2.078], ['FCO', 'Rome', 41.8, 12.239],
  ['AGP', 'Malaga', 36.675, -4.499], ['PMI', 'Palma', 39.552, 2.739], ['LIS', 'Lisbon', 38.774, -9.134],
  ['ATH', 'Athens', 37.936, 23.947], ['IST', 'Istanbul', 41.275, 28.752], ['CPH', 'Copenhagen', 55.618, 12.656],
  ['DXB', 'Dubai', 25.253, 55.364], ['DOH', 'Doha', 25.273, 51.608], ['CAI', 'Cairo', 30.122, 31.406],
  ['RAK', 'Marrakesh', 31.607, -8.036], ['JFK', 'New York', 40.641, -73.778], ['BOS', 'Boston', 42.366, -71.01],
  ['LAX', 'Los Angeles', 33.942, -118.408], ['YYZ', 'Toronto', 43.677, -79.625], ['DEL', 'Delhi', 28.556, 77.1],
  ['BOM', 'Mumbai', 19.09, 72.866], ['SIN', 'Singapore', 1.364, 103.991], ['HKG', 'Hong Kong', 22.308, 113.918],
  ['NRT', 'Tokyo', 35.772, 140.393], ['SYD', 'Sydney', -33.94, 151.175], ['JNB', 'Johannesburg', -26.139, 28.246],
  ['NBO', 'Nairobi', -1.319, 36.928], ['GRU', 'Sao Paulo', -23.435, -46.473],
];
export const UK_AIRPORTS = new Set(['LHR', 'LGW', 'MAN', 'EDI', 'GLA', 'BHX', 'BRS', 'BFS']);
