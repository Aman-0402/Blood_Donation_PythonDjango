import OrgProfileForm from '../../components/OrgProfileForm'
import { createBankProfile, getMyBankProfile, updateBankProfile } from '../../services/bloodbanks'

const service = { get: getMyBankProfile, create: createBankProfile, update: updateBankProfile }

function BankProfile() {
  return <OrgProfileForm noun="Blood bank" service={service} />
}

export default BankProfile
