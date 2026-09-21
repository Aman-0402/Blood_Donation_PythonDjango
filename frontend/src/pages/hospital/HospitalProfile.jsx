import OrgProfileForm from '../../components/OrgProfileForm'
import { createHospitalProfile, getMyHospitalProfile, updateHospitalProfile } from '../../services/hospitals'

const service = { get: getMyHospitalProfile, create: createHospitalProfile, update: updateHospitalProfile }

function HospitalProfile() {
  return <OrgProfileForm noun="Hospital" service={service} />
}

export default HospitalProfile
