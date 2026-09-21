export const NAV_ITEMS = {
  admin: [{ to: '/admin', label: 'Dashboard', end: true }],
  donor: [
    { to: '/donor', label: 'Dashboard', end: true },
    { to: '/donor/profile', label: 'My profile' },
    { to: '/donor/donations', label: 'Donation history' },
  ],
  seeker: [{ to: '/seeker', label: 'Dashboard', end: true }],
  hospital: [{ to: '/hospital', label: 'Dashboard', end: true }],
  bloodbank: [{ to: '/bloodbank', label: 'Dashboard', end: true }],
}
