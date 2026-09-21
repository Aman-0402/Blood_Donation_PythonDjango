export const NAV_ITEMS = {
  admin: [
    { to: '/admin', label: 'Dashboard', end: true },
    { to: '/admin/requests', label: 'Blood requests' },
    { to: '/admin/hospitals', label: 'Hospitals' },
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
  bloodbank: [{ to: '/bloodbank', label: 'Dashboard', end: true }],
}
