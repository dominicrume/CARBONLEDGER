// Example partners for the demo. Fictional names; partners pay the trustee price and the CLT is issued to the user.
export const PARTNERS = [
  { id: 'search', name: 'Wayfind Search', kind: 'Search engine', action: 'Run 50 searches', grams: 120, note: 'Funded from search ad revenue' },
  { id: 'coffee', name: 'Groundwork Coffee', kind: 'Café loyalty scheme', action: 'Buy a coffee in a reusable cup', grams: 40, note: 'Swaps loyalty points for grams' },
  { id: 'bikes', name: 'Pedal Share', kind: 'Bike hire', action: 'Ride 10 km', grams: 250, note: 'Rewards trips that replace car journeys' },
];

// Example league entries, shown labelled as examples next to the viewer's own total.
export const EXAMPLE_PLAYERS = [
  { name: 'Amira (example)', grams: 182400, league: 'Individuals' },
  { name: 'Tom (example)', grams: 64200, league: 'Individuals' },
  { name: 'Leeds Climate Club (example)', grams: 2410000, league: 'Groups' },
  { name: 'Hartley Bakery Ltd (example)', grams: 7350000, league: 'Businesses' },
];

// Example businesses for the business league.
export const EXAMPLE_BUSINESSES = [
  { name: 'Hartley Bakery Ltd (example)', grams: 7350000, employees: 18 },
  { name: 'Northgate Architects (example)', grams: 21400000, employees: 42 },
  { name: 'Brightwell Logistics (example)', grams: 186000000, employees: 310 },
  { name: 'Fernhill Dental Practice (example)', grams: 2900000, employees: 9 },
];
