export const ROLES = {
  ADMIN: 'admin',
  DONOR: 'donor',
  SEEKER: 'seeker',
  HOSPITAL: 'hospital',
  BLOODBANK: 'bloodbank',
}

export const REGISTER_ROLES = [
  { value: ROLES.DONOR, label: 'Donor' },
  { value: ROLES.SEEKER, label: 'Blood seeker / patient' },
  { value: ROLES.HOSPITAL, label: 'Hospital' },
  { value: ROLES.BLOODBANK, label: 'Blood bank' },
]

export const roleHome = (role) => `/${role}`
