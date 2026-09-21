export const NAV_ITEMS = {
  admin: [
    { to: '/admin', label: 'Dashboard', end: true },
    { to: '/admin/requests', label: 'Blood requests' },
    { to: '/admin/hospitals', label: 'Hospitals' },
    { to: '/admin/bloodbanks', label: 'Blood banks' },
  ],
  donor: [
    { to: '/donor', label: 'Dashboard', end: true },
    { to: '/donor/profile', label: 'My profile' },
    { to: '/donor/donations', label: 'Donation history' },
  ],
  seeker: [
    { to: '/seeker', label: 'Dashboard', end: true },
    { to: '/seeker/requests', label: 'My requests', end: true },
    { to: '/seeker/requests/new', label: 'New request' },
  ],
  hospital: [
    { to: '/hospital', label: 'Dashboard', end: true },
    { to: '/hospital/profile', label: 'Hospital profile' },
    { to: '/hospital/availability', label: 'Blood availability' },
    { to: '/hospital/requests', label: 'Blood requests', end: true },
    { to: '/hospital/requests/new', label: 'New request' },
  ],
  bloodbank: [
    { to: '/bloodbank', label: 'Stock overview', end: true },
    { to: '/bloodbank/profile', label: 'Blood bank profile' },
    { to: '/bloodbank/inventory', label: 'Inventory' },
    { to: '/bloodbank/issue', label: 'Issue blood' },
    { to: '/bloodbank/history', label: 'Inventory history' },
    { to: '/bloodbank/requests', label: 'Requests' },
  ],
}
